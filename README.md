# Objective-C Autocomplete (pre-alpha)

# Note
These are thrown together. I use them on my own internal projects so when I have
a free moment, I put a little bit together. It's not extensive.

## Automatic Header lookup

Typing `#import` will trigger a look up of all `.h` files in the working 
directory of the file referenced. This works for most projects, but could 
probably be expanded.

## Declared methods lookup

Typing `- (<char>)` will look up the header for the current `.m` filename and offer 
auto-fills for the methods declared in the header. 
Responses will be in snippet format so you can tab through the options.

# Useful things

Try mixing with https://github.com/echoldman/Sublime-Text-Objective-C-Snippets 
for extra helpfulness.