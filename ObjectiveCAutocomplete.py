import os
import os.path
import sys
import fnmatch
import sublime
import sublime_plugin
import re

class ObjectiveCHeaderAutoCompleteTextCommand(sublime_plugin.TextCommand):
  def run(self, view, args):
    quote_edit = view.begin_edit()
    # insert the space and quote
    view.insert(quote_edit, full_line_region.end()-1, ' "')
    view.end_edit(quote_edit)

class ObjectiveCHeaderAutoComplete(sublime_plugin.EventListener):
  def on_query_completions(self, view, prefix, locations):
    # if this isn't objc or c then we should bail
    scope_name = view.scope_name(locations[0])

    if scope_name.find('source.objc') != 0 and scope_name.find('source.c') != 0:
      return None

    # only hit the filesystem if this is an import line
    full_line_region = view.full_line(locations[0])
    full_line = view.substr(full_line_region)
    import_line_math = r'#(import|include)(\s+?)(\"|$)(.*?|$)(\"|$)'
    matches = re.match(import_line_math, full_line)
    if matches:
      groups = matches.groups()
      prefix_length = len(groups[0]) + 1 # +1 for the hash
      if len(groups) > 1:
        prefix_length += len(groups[1]) # for the spaces
      if len(groups) > 2:
        prefix_length += len(groups[2]) # for the quote or whatever
      if len(groups) > 3:
        file_name_so_far = groups[3]
      else:
        file_name_so_far = ''

      length = len(file_name_so_far)
      print(file_name_so_far)
      if length > 0:
        if file_name_so_far[length-1] == '"':
          file_name_so_far = file_name_so_far[0:len(file_name_so_far)-1]

      if full_line == '#import\n' or full_line == '#include\n':
        view.run_command('objective_c_header_auto_complete')

      working_dir = os.path.dirname(view.file_name())
      # loop recursively through sub directories
      headers = [os.path.join(dirpath, f).replace(working_dir+'/', '')
                   for dirpath, dirnames, files in os.walk(working_dir) 
                   for f in fnmatch.filter(files, file_name_so_far+'*.h')]

      # sublime.INHIBIT_WORD_COMPLETIONS inhibits unwanted completions here
      triggers = [(header_file, header_file) for header_file in headers]
      return (triggers, sublime.INHIBIT_WORD_COMPLETIONS)

    return None


class ObjectiveCDeclaredMethodAutoCompleteTextCommand(sublime_plugin.TextCommand):
  def run(self, view, args):
    paren_edit = view.begin_edit()
    view.erase(paren_edit, args[0])
    view.end_edit(paren_edit)

class ObjectiveCDeclaredMethodAutoComplete(sublime_plugin.EventListener):
  def on_query_completions(self, view, prefix, locations):
    # if this isn't objc or c then we should bail
    scope_name = view.scope_name(locations[0])

    if scope_name.find('source.objc') != 0:
      return None

    # don't look up things for headers.
    if os.path.splitext(view.file_name())[1] == '.h' or os.path.splitext(view.file_name())[1] == '.hpp':
      return None

    # only hit the filesystem if this is a new method line
    full_line_region = view.full_line(locations[0])
    full_line = view.substr(full_line_region)
    last_char = full_line[len(full_line)-2]
    ends_in_parenthesis = last_char == ')'

    if last_char == ';' or last_char == '{':
      # in snippet mode most likely, so just return
      return
    
    # only look up methods if this is a line for a method
    method_line_search = r'(\-|\+)(\s*?)(\(|$)'
    matches = re.match(method_line_search, full_line)
    if matches:
      groups = matches.groups()

      # find the header for this file
      header_file = os.path.splitext(view.file_name())[0] + '.h'
      methods = extract_objc_methods(header_file)
      param_name_search = re.compile(r'\:(\s*)\((.+?)\)(\s+)(.+?)(\s|;)')
      triggers = []
      for method in methods:
        # print(method)
        snippet, param_count = re.subn(param_name_search, r'\1(\2)\3${{SNIPPET_NUMBER}:\4}\5', method)
        for i in range(0,param_count):
          snippet = snippet.replace('{SNIPPET_NUMBER}', str(i+1), 1)
        # at this point the user should have some parenthesis, so delete any leading things
        if ends_in_parenthesis:
          snippet = snippet.replace(full_line[0:len(full_line)-3], '')
        else:
          snippet = snippet.replace(full_line[0:len(full_line)-2], '')

        triggers.append((method, snippet))

      if full_line.find('- (') == 0 and ends_in_parenthesis:
        # delete that last paranthesis
        view.run_command('objective_c_declared_method_auto_complete', sublime.Region(locations[0], locations[0]+1))

      return (triggers, sublime.INHIBIT_WORD_COMPLETIONS)

    return None

class ObjectiveCSynthesizeAutoComplete(sublime_plugin.EventListener):
  def on_query_completions(self, view, prefix, locations):
    # if this isn't objc or c then we should bail
    scope_name = view.scope_name(locations[0])

    if scope_name.find('source.objc') != 0:
      return None

    # don't look up things for headers.
    if os.path.splitext(view.file_name())[1] == '.h' or os.path.splitext(view.file_name())[1] == '.hpp':
      return None

    # only hit the filesystem if this is a new method line
    full_line_region = view.full_line(locations[0])
    full_line = view.substr(full_line_region)

    # only look up methods if this is a line for a synthesize
    synthesize_line_search = r'\s*@synthesize '
    matches = re.match(synthesize_line_search, full_line)
    if matches:
      header_file = os.path.splitext(view.file_name())[0] + '.h'
      properties = extract_objc_properties(header_file)

      triggers = []
      for prop in properties:
        parts = prop.split(' ')
        if len(parts) > 0:
          name = parts[-1];
          triggers.append((prop, name.replace('*', '')));

      return triggers;

    return None

def extract_objc_properties(file_path):
  results = []
  # open the file
  fh = open(file_path, 'r')
  header = fh.read()
  fh.close()

  method_line_search = re.compile(r'@property\s*(?:\(.+?\)|)(.+?);', re.MULTILINE + re.DOTALL)
  matches = re.findall(method_line_search, header)

  for match in matches:
    line = re.sub(r'\\(\s+)', ' ', match)
    line = re.sub(r'  ', ' ', line)
    results.append(line)

  # get all the lines
  return results

def extract_objc_methods(file_path):
  results = []
  # open the file
  fh = open(file_path, 'r')
  header = fh.read()
  fh.close()

  method_line_search = re.compile(r'^(?:\-|\+)(?:\s*)(?:\()(?:.*?)(?:\))(?:\s*)(?:.+?);', re.MULTILINE + re.DOTALL)
  matches = re.findall(method_line_search, header)

  for match in matches:
    line = re.sub(r'\\(\s+)', ' ', match)
    line = re.sub(r'  ', ' ', line)
    results.append(line)

  # get all the lines
  return results


