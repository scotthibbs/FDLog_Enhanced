"""
Standalone Call Sign Parser Module
Copyright (c) 2022 by Scott Anthony Hibbs KD4SIR
Released under a GPLv3 License.

This module provides call sign parsing functionality that can be used
as a library or imported by GUI applications.
"""

import os
import re
import urllib.request
import urllib.error
from datetime import datetime

# URL for the cty.dat file
CTY_DAT_URL = "https://www.country-files.com/cty/cty.dat"


class CallSignParserError(Exception):
    """Base exception for CallSignParser errors."""
    pass


class CtyFileNotFoundError(CallSignParserError):
    """Raised when cty.dat file cannot be found."""
    pass


class CtyFileReadError(CallSignParserError):
    """Raised when cty.dat file cannot be read."""
    pass


class InvalidCallSignError(CallSignParserError):
    """Raised when an invalid call sign is provided."""
    pass


class CtyDownloadError(CallSignParserError):
    """Raised when cty.dat cannot be downloaded."""
    pass


class CallSignParser:
    """Takes a call sign and returns prefix, separator, suffix, country and valid prefix check."""

    # Class variable to cache the parsed cty.dat data
    _cty_cache = None

    def __init__(self):
        pass

    @staticmethod
    def _reverse_list(input_list):
        """Reverses the order of a list."""
        return input_list[::-1]

    @staticmethod
    def _validate_callsign(callsign):
        """Validate that the input is a valid call sign format."""
        if callsign is None:
            raise InvalidCallSignError("Call sign cannot be None")

        if isinstance(callsign, list):
            callsign = ''.join(callsign)

        callsign = str(callsign).strip()

        if len(callsign) == 0:
            raise InvalidCallSignError("Call sign cannot be empty")

        if len(callsign) < 3:
            raise InvalidCallSignError("Call sign must be at least 3 characters")

        # Check for at least one letter and one digit (basic call sign requirement)
        has_letter = any(c.isalpha() for c in callsign)
        has_digit = any(c.isdigit() for c in callsign)

        if not has_letter:
            raise InvalidCallSignError("Call sign must contain at least one letter")

        if not has_digit:
            raise InvalidCallSignError("Call sign must contain at least one digit")

        return callsign

    @staticmethod
    def parse_callsign(callsign):
        """
        Parse a call sign and return the prefix, separator digit, and suffix.

        Args:
            callsign: The call sign string or list of characters to parse

        Returns:
            tuple: (prefix, separator, suffix) as strings

        Raises:
            InvalidCallSignError: If the call sign is invalid
        """
        # Convert to list if string
        if isinstance(callsign, str):
            tryfix = list(callsign)
        else:
            tryfix = callsign

        # Reverse the call sign to find the suffix
        prefsuf = CallSignParser._reverse_list(tryfix)

        # Create lists for the suffix and prefix
        suffix = []
        prefix = []

        # Numbers used to find the separator
        numbers = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']

        # Counters for tracking position
        counter3 = 0  # separator counter
        counter4 = 0  # number counter in case of slash

        # Count how many digits are in the call sign
        questdig = sum(c1.isdigit() for c1 in tryfix)

        # Call signs that start with numbers need adjustment
        str1letter = tryfix[0]
        if str1letter.isdigit():
            questdig = questdig - 1

        # Check for slashes first
        if "/" in tryfix or "\\" in tryfix:
            for item1 in prefsuf:
                if item1 == "/" or item1 == "\\":
                    suffix.pop(counter4)
                    continue
                else:
                    counter4 -= 1  # increment backwards for slash removal
                if item1.isdigit():
                    if questdig == 1:
                        counter3 += 1  # separator trigger
                    else:
                        questdig -= 1  # reduce the count
                if counter3 < 1:
                    suffix.append(item1)
                else:
                    prefix.append(item1)
        else:
            # No slashes - append suffix until a number, then rest is prefix
            for item in prefsuf:
                if item in numbers:
                    counter3 += 1
                if counter3 < 1:
                    suffix.append(item)
                else:
                    prefix.append(item)

        # Separate the separator digit from the prefix
        separator_digit = [prefix[0]]
        str_separator = ''.join(separator_digit)  # Fixed: was str(separator_digit)

        # Set the prefix to read forward and remove the separator
        prefix = CallSignParser._reverse_list(prefix)
        del prefix[-1]

        # Set the suffix to read forward
        suffix = CallSignParser._reverse_list(suffix)

        # Join list values into strings
        str_prefix = ''.join(prefix)
        str_suffix = ''.join(suffix)

        return str_prefix, str_separator, str_suffix

    @classmethod
    def _load_cty_file(cls):
        """
        Load and parse the cty.dat file, caching the results.

        Returns:
            dict: Dictionary mapping country names to their prefixes

        Raises:
            CtyFileNotFoundError: If cty.dat cannot be found
            CtyFileReadError: If cty.dat cannot be read
        """
        # Return cached data if available
        if cls._cty_cache is not None:
            return cls._cty_cache

        # Build path relative to this module's location
        module_dir = os.path.dirname(__file__)
        cty_path = os.path.join(module_dir, "cty.dat")

        if not os.path.exists(cty_path):
            raise CtyFileNotFoundError(
                f"cty.dat file not found at: {cty_path}\n"
                "Download from: https://www.country-files.com/category/big-cty/"
            )

        dictdx = {}
        thisnow = ""

        try:
            with open(cty_path, "r", encoding="utf-8", errors="replace") as cty_file:
                for lnx in cty_file:
                    if not lnx:
                        continue

                    if re.match(r'\w', lnx):
                        # This is a country name line
                        thisnow = lnx.split(':')[0]
                        dictdx[thisnow] = []
                    else:
                        # This is a prefix data line
                        datapref = lnx.split(',')
                        # Clean up: remove semicolon, spaces, newlines, brackets and parentheses with numbers
                        datapref2 = [re.sub(';', '', item) for item in datapref]
                        datapref3 = [re.sub(' ', '', item) for item in datapref2]
                        datapref4 = [re.sub('\n', '', item) for item in datapref3]
                        datapref5 = [re.sub(r"\[\d*?]", '', item) for item in datapref4]
                        datapref6 = [re.sub(r"\(\d*?\)", '', item) for item in datapref5]
                        if thisnow in dictdx:
                            dictdx[thisnow].append(datapref6)
        except IOError as e:
            raise CtyFileReadError(f"Error reading cty.dat: {e}")

        # Cache the result
        cls._cty_cache = dictdx
        return dictdx

    @classmethod
    def clear_cache(cls):
        """Clear the cached cty.dat data."""
        cls._cty_cache = None

    @classmethod
    def get_cty_file_path(cls):
        """Get the full path to the cty.dat file."""
        module_dir = os.path.dirname(__file__)
        return os.path.join(module_dir, "cty.dat")

    @classmethod
    def get_cty_file_age_days(cls):
        """
        Get the age of the cty.dat file in days.

        Returns:
            int: Age in days, or -1 if file doesn't exist
        """
        cty_path = cls.get_cty_file_path()
        if not os.path.exists(cty_path):
            return -1

        modified_time = os.path.getmtime(cty_path)
        modified_date = datetime.fromtimestamp(modified_time)
        age = datetime.now() - modified_date
        return age.days

    @classmethod
    def get_cty_file_date(cls):
        """
        Get the modification date of the cty.dat file as a formatted string.

        Returns:
            str: Date string (e.g., "January 22, 2026") or "Not found"
        """
        cty_path = cls.get_cty_file_path()
        if not os.path.exists(cty_path):
            return "Not found"

        modified_time = os.path.getmtime(cty_path)
        modified_date = datetime.fromtimestamp(modified_time)
        return modified_date.strftime("%B %d, %Y")

    @classmethod
    def download_cty_file(cls):
        """
        Download the latest cty.dat file from country-files.com.

        Returns:
            bool: True if download was successful

        Raises:
            CtyDownloadError: If download fails
        """
        cty_path = cls.get_cty_file_path()

        try:
            # Download the file
            req = urllib.request.Request(
                CTY_DAT_URL,
                headers={'User-Agent': 'CallSignParser/1.0'}
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                data = response.read()

            # Write to file
            with open(cty_path, 'wb') as f:
                f.write(data)

            # Clear the cache so the new file gets loaded
            cls.clear_cache()

            return True

        except urllib.error.URLError as e:
            raise CtyDownloadError(f"Network error: {e.reason}")
        except urllib.error.HTTPError as e:
            raise CtyDownloadError(f"HTTP error {e.code}: {e.reason}")
        except IOError as e:
            raise CtyDownloadError(f"File write error: {e}")

    @classmethod
    def lookup_country(cls, checkprefix, separator):
        """
        Look up the country for a given prefix in the cty.dat file.

        Args:
            checkprefix: The call sign prefix to look up
            separator: The separator digit

        Returns:
            str: The country name or "unassigned?"

        Raises:
            CtyFileNotFoundError: If cty.dat cannot be found
            CtyFileReadError: If cty.dat cannot be read
        """
        dictdx = cls._load_cty_file()

        # Needs to be upper to match the cty.dat file
        final = checkprefix.upper()

        # Handle exceptions for single letter country calls
        if len(final) > 0:
            final1 = final[0]
            singles = ['B', 'F', 'G', 'I', 'K', 'M', 'N', 'R', 'W']

            if final1 in singles:
                final = final[0]

            # Exception for A prefix calls
            if final1 == "A":
                if len(final) > 1:
                    final2 = final[1]
                    if final2.isdigit():
                        final = final1 + final2
                    elif final2 == "":
                        final = final1 + separator
                    else:
                        final = final1 + final2
                else:
                    final = final1 + separator

        # Find the prefix in the dictionary
        country = [key for key, val in dictdx.items() if any(final in s for s in val)]

        if len(country) == 0:
            # Try with separator appended
            final_with_sep = final + separator
            country = [key for key, val in dictdx.items() if any(final_with_sep in s for s in val)]
            if len(country) == 0:
                return "unassigned?"

        # Clean up the result
        country_str = str(country)
        country_str = re.sub(r"[\[\]]", '', country_str)
        country_str = country_str.replace("'", "")

        return country_str

    @staticmethod
    def is_valid_prefix(country):
        """
        Check if the country lookup result indicates a valid prefix.

        Args:
            country: The country string from lookup_country()

        Returns:
            bool: True if valid, False otherwise
        """
        return country not in ("unassigned?", "")

    @classmethod
    def parse(cls, callsign):
        """
        Parse a call sign and return all information.

        This is the main entry point for parsing call signs.

        Args:
            callsign: The call sign to parse (string or list)

        Returns:
            tuple: (prefix, separator, suffix, country, is_valid)

        Raises:
            InvalidCallSignError: If the call sign is invalid
            CtyFileNotFoundError: If cty.dat cannot be found
            CtyFileReadError: If cty.dat cannot be read
        """
        # Validate input
        validated = cls._validate_callsign(callsign)

        # Parse the call sign
        prefix, separator, suffix = cls.parse_callsign(validated)

        # Look up the country
        country = cls.lookup_country(prefix, separator)

        # Check if valid
        is_valid = cls.is_valid_prefix(country)

        return prefix, separator, suffix, country, is_valid


# Convenience function for simple usage
def parse_callsign(callsign):
    """
    Parse a call sign and return all information.

    Args:
        callsign: The call sign to parse

    Returns:
        tuple: (prefix, separator, suffix, country, is_valid)
    """
    return CallSignParser.parse(callsign)
