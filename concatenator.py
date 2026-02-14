class MyStringConcatenator:
    """
    A simple node to concatenate two strings.
    """
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "string1": ("STRING", {"default": "", "multiline": True}),
                "string2": ("STRING", {"default": "", "multiline": True}),
            },
            "optional": {
                "delimiter": ("STRING", {"default": "", "multiline": False}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("result",)
    FUNCTION = "concatenate_strings"
    CATEGORY = "Crytus/Text"

    def concatenate_strings(self, string1, string2, delimiter=""):
        return (string1 + delimiter + string2,)

# Dictionary that maps the class name to the node class
NODE_CLASS_MAPPINGS = {
    "MyStringConcatenator": MyStringConcatenator
}

# Dictionary that maps the internal class name to the display name in the UI
NODE_DISPLAY_NAME_MAPPINGS = {
    "MyStringConcatenator": "Simple String Concatenator"
}
