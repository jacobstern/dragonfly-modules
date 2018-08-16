import re
import urllib2
import json

from dragonfly import *


def _emacs_function_rpc(name, args):
    request = urllib2.Request('http://192.168.56.1:8010/call-function')
    request.add_header('Content-Type', 'application/json')
    payload = {'name': name, 'args': args}
    try:
        response = urllib2.urlopen(request, json.dumps(payload))
    except Exception as e:
        print "Connection error: " + str(e)
    return json.load(response)


class EmacsFunctionNonDynamic(ActionBase):
    def __init__(self, name, *args):
        ActionBase.__init__(self)
        self._name = name
        self._args = args

    def _execute(self, data):
        _emacs_function_rpc(self._name, self._args)


class EmacsFunction(ActionBase):
    def __init__(self, name, *args):
        ActionBase.__init__(self)
        self._name = name
        self._args = args

    def _execute(self, data):
        _emacs_function_rpc(self._name, [data[a] for a in self._args])


class EmacsMacro(ActionBase):
    def __init__(self, macro):
        ActionBase.__init__(self)
        self._macro = macro

    def _execute(self, _):
        _emacs_function_rpc("dictation/send-macro", [self._macro])


class EmacsKey(ActionBase):
    def __init__(self, sequence):
        ActionBase.__init__(self)
        self._sequence = sequence

    def _execute(self, _):
        _emacs_function_rpc("dictation/send-key-sequence", [self._sequence])


class EmacsText(ActionBase):
    def __init__(self, template):
        ActionBase.__init__(self)
        self._template = template

    def _execute(self, data=None):
        if data:
            value = self._template % data
        else:
            value = self._template
        _emacs_function_rpc("insert", [value])


def format_pascal(words):
    return "".join(word.capitalize() for word in words)


def format_snake(words):
    return "_".join(word.lower() for word in words)


def format_kebab(words):
    return "-".join(word.lower() for word in words)


format_function_map = {
    "cally": format_pascal,
    "snake": format_snake,
    "Bobby": format_kebab,
}


def strip_dragon_annotations(word):
    """
    Remove special annotations from Dragon recognition.
    """
    return re.sub(r"\\\w+(-\w+)?", "", word)


def process_format_words(words):
    """
    Sanitize recognition results for a format function. Groups adjacent letters
    into the same formatted word.
    """
    letters = ""
    processed_words = []
    for word in words:
        word = strip_dragon_annotations(word)
        word = re.sub(r"\W+", "", word) # Remove non-alphanumeric
        letter = None
        if word.lower() in letters_map:
            letter = letters_map[word.lower()]
        elif len(word) == 1:
            letter = word
        if letter:
            letters += letter
        elif word:
            if letters:
                processed_words.append(letters)
                letters = ""
            processed_words.append(word)
    if letters:
        processed_words.append(letters)
    return processed_words
 

letters_map = {
    "alpha": "a",
    "bravo": "b",
    "charlie": "c",
    "delta": "d",
    "echo": "e",
    "foxtrot": "f",
    "golf": "g",
    "hotel": "h",
    "india": "i",
    "juliet": "j",
    "kilo": "k",
    "lima": "l",
    "mike": "m",
    "november": "n",
    "oscar": "o",
    "papa": "p",
    "quebec": "q",
    "romeo": "r",
    "sierra": "s",
    "tango": "t",
    "uniform": "u",
    "victor": "v",
    "whiskey": "w",
    "x-ray": "x",
    "yankee": "y",
    "zulu": "z",
}


class RadioSpellingCharacterRule(MappingRule):
    mapping = letters_map


def print_radio_character(character):
    EmacsText(character).execute()


class RadioSpellingRule(MappingRule):
    mapping = {
        "<character>": Function(print_radio_character),
    }
    extras = [
        RuleRef(RadioSpellingCharacterRule(), "character"),
    ]


def format_words(formatter, text):
    raw_words = text.words
    words = process_format_words(raw_words)
    EmacsText(formatter(words)).execute()


class FormatRule(MappingRule):
    mapping = {
        "<formatter> <text>": Function(format_words),
    }
    extras = [
        Choice("formatter", format_function_map),
        Dictation("text"),
    ]


class NumericLiteralRule(MappingRule):
    mapping = {
        "numb <n>": EmacsText("%(n)d"),
    }
    extras = [
        IntegerRef("n", 0, 10000),
    ]


class PunctuationRule(MappingRule):
    mapping = {
        "ace": EmacsText(" "),
        "Porter": EmacsText("\""),
        "Singer": EmacsText("'"),
        "Perry": EmacsKey("("),
        "final Perry": EmacsText(")"),
        "deckle": EmacsText(":"),
        "drip": EmacsText(","),
        "indie": EmacsText("["),
        "final indie": EmacsText("]"),
        "Sarah": EmacsText("<"),
        "final Sarah": EmacsText(">"),
        "Sentinel": EmacsText("%%"),
        "Curly": EmacsText("{"),
        "final curly": EmacsText("}"),
        "equals": EmacsText("="),
        "dot": EmacsText("."),
        "minus|dashing": EmacsText("-"),
        "underscore": EmacsText("_"),
        "Starling": EmacsText("*"),
    }
    extras = [
        IntegerRef("n", 1, 100),
    ]
    defaults = {
        "n": 1,
    }


class EmacsInnerLoopCommandsRule(MappingRule):
    mapping = {
        "slap": EmacsKey("\r"),
        "liner [<n>]": EmacsFunction("newline", "n"),
        "seeking [<line>]": EmacsFunction("goto-line", "line"),
        "tabby": EmacsFunction("indent-for-tab-command"),
        "clear [<n>]": EmacsFunction("delete-backward-char", "n"),
        "deli [<n>]": EmacsFunction("delete-char", "n"),
        "ross [<n>]": EmacsFunction("forward-char", "n"),
        "lease [<n>]": EmacsFunction("backward-char", "n"),
        "dunce [<n>]": EmacsFunction("next-line", "n"),
        "sauce [<n>]": EmacsFunction("previous-line", "n"),
        "Homer [<n>]": EmacsFunction("back-to-indentation"),
        "Cali  [<n>]": EmacsFunction("move-beginning-of-line", "n"),
        "Merrill [<n>]": EmacsFunction("move-end-of-line", "n"),
        "marking": EmacsFunctionNonDynamic("push-mark", None, None, True),
    }
    extras = [
        IntegerRef("n", 1, 100),
        IntegerRef("line", 1, 100000),
    ]
    defaults = {
        "n": 1,
    }


class VerbatimRule(MappingRule):
    mapping = {
        "say <text>": EmacsText("%(text)s"),
    }
    extras = [
        Dictation("text"),
    ]


class EmacsGeneralCommandsRule(MappingRule):
    mapping = {
        "scratch that": EmacsFunction("undo"),
        "quit": EmacsKey("C-g"),
        "save buffer": EmacsFunction("save-buffer"),
        "scroll down": EmacsFunction("scroll-down"),
        "scroll up": EmacsFunction("scroll-up"),
    }


inner_loop_alternatives = [
    RuleRef(PunctuationRule()),
    RuleRef(EmacsInnerLoopCommandsRule()),
    RuleRef(RadioSpellingRule()),
    RuleRef(VerbatimRule()),
    RuleRef(FormatRule()),
    RuleRef(NumericLiteralRule()),
]


inner_loop_element = Alternative(inner_loop_alternatives)


class RepeatRule(CompoundRule):
    spec = "<sequence> [[[and] repeat [that]] <n> times]"
    extras = [
        Repetition(inner_loop_element, min=1, max=16, name="sequence"),
        IntegerRef("n", 1, 100),
    ]
    defaults = {
        "n": 1,
    }

    def _process_recognition(self, node, extras):
        sequence = extras["sequence"]
        count = extras["n"]
        for i in range(count):
            for action in sequence:
                action.execute()


emacs_grammar = Grammar("emacs")
emacs_grammar.add_rule(EmacsGeneralCommandsRule())
emacs_grammar.add_rule(RepeatRule())
emacs_grammar.load()
emacs_grammar.set_exclusiveness(1) # While active, suppress default Dragon grammar


def disable_exclusive_grammars():
    global emacs_grammar
    global management_grammar
    if emacs_grammar:
        emacs_grammar.disable()
        emacs_grammar.set_exclusiveness(0)
    if management_grammar:
        management_grammar.set_exclusiveness(0)


def enable_exclusive_grammars():
    global emacs_grammar
    global management_grammar
    if emacs_grammar:
        emacs_grammar.enable()
        emacs_grammar.set_exclusiveness(1)
    if management_grammar:
        management_grammar.set_exclusiveness(1)


class ManagementRule(MappingRule):
    mapping = {
        "back to Dragon": Function(disable_exclusive_grammars),
        "assuming control": Function(enable_exclusive_grammars),
    }


management_grammar = Grammar("management")
management_grammar.add_rule(ManagementRule())
management_grammar.load()
management_grammar.set_exclusiveness(1)


def unload():
    global emacs_grammar
    global management_grammar
    if emacs_grammar:
        emacs_grammar.unload()
    if management_grammar:
        management_grammar.unload()
    emacs_grammar = None
    management_grammar = None
