import subprocess

def num_to_letter(number):
    """
    Converts a number to a letter.

    :param number: integer
    """
    return chr(65 + (number - 1) % 26)

def num_to_two_letters(number):
    """
    Converts a number to a two-letter string.

    :param number: integer
    """
    if number > 26*26:
        raise NotImplementedError('The allowed domain is 1 to %d' % 26*26)
    from math import ceil
    first_letter = num_to_letter(ceil(number/26))
    second_letter = num_to_letter(number)
    return first_letter + second_letter

def num_to_three_letters(number):
    """
    Converts a number to a three-letter string.

    :param number: integer
    """
    if number > 26**3:
        raise NotImplementedError('The allowed domain is 1 to %d' % 26**3)
    from math import ceil
    scalar = ceil(number / 26**2)
    first_letter = num_to_letter(scalar)
    second_third_letter = num_to_two_letters(number - ((scalar - 1)* 26**2))
    return first_letter + second_third_letter

def write_to_log(cmd, logfile):
    """
    Saves output of a terminal command to a file.

    :param cmd: array
    :param logfile: file
    """
    proc = subprocess.Popen(cmd,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in proc.stdout:
        logfile.write(line.decode('utf-8'))
    proc.wait()
    return logfile
