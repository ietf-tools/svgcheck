# ----------------------------------------------------
# Copyright The IETF Trust 2018-9, All Rights Reserved
# ----------------------------------------------------

try:
    import curses
    haveCurses = True
except ImportError:
    haveCurses = False

import codecs
import six
import re
from rfctools_common import log


def ReplaceWithONE(exc):
    if isinstance(exc, UnicodeDecodeError):
        return u'\u0001'
    elif isinstance(exc, UnicodeEncodeError):
        if six.PY2:
            return ((exc.end - exc.start) * u'\u0001', exc.end)
        else:
            return (bytes((exc.end - exc.start) * [1]), exc.end)
    else:
        raise TypeError("can't handle %s" % type(exc).__name__)


class CursesCommon(object):
    def __init__(self, config):
        self.no_curses = False
        self.curses = None

        self.interactive = False

        if config.options.output_filename is not None:
            self.interactive = True
        codecs.register_error('replaceWithONE', ReplaceWithONE)

        self.skipArtwork = config.options.skip_artwork
        self.skipCode = config.options.skip_code

    def initscr(self):
        self.A_REVERSE = 1
        self.A_NORMAL = 0
        if self.interactive and not self.no_curses:
            if haveCurses:
                try:
                    self.curses = curses.initscr()
                    curses.start_color()
                    curses.noecho()
                    curses.cbreak()
                    self.spaceline = " "*curses.COLS
                    self.A_REVERSE = curses.A_REVERSE
                    self.A_NORMAL = curses.A_NORMAL
                except curses.error as e:
                    if self.curses:
                        self.endwin()
                    self.curses = None
                    log.error("Problem loading curses - " + e)
            else:
                log.warn("Unable to load CURSES for python")

    def endwin(self):
        if self.curses:
            try:
                curses.nocbreak()
                curses.echo()
                curses.endwin()
                self.curses = None
            except curses.error:
                pass

    def writeStringInit(self):
        self.lines = []
        self.hilight = []

    def writeString(self, text, color=0, partialString=False):
        newLine = False
        cols = 80
        if self.curses:
            cols = curses.COLS
            if color == 0:
                color = curses.A_NORMAL
        saveX = self.x
        saveY = self.y

        if self.y == 0 and self.x == 0:
            text = text.lstrip()
        text = re.sub(r'\s*\n\s*', ' ',
                      re.sub(r'\.\s*\n\s*', '.  ',
                             text))
        # if len(text) > 0 and text[-1] != ' ':
        #     text += ' '

        if six.PY2:
            text = text.encode('ascii', 'replaceWithONE')
        for line in text.splitlines(1):
            if line[-1:] == '\n':
                newLine = True
                line = line[:-1]
            while self.x + len(line) >= cols-1:
                p = line[:cols - self.x - 2] + "\\"
                if self.x:
                    self.lines[-1] += p
                else:
                    self.lines.append(p)
                line = line[cols-self.x-2:]
                self.x = 0
                self.y += 1
            if self.x == 0:
                self.lines.append(line)
            else:
                self.lines[-1] += line
            self.x += len(line)
            if newLine:
                if self.x != 0:
                    self.x = 0
                self.y += 1
                newLine = False
            # if self.x != 0 and line[-1] != ' ' and not partialString:
            #     self.lines[-1] += " "
        if color == self.A_REVERSE:
            self.reverse = [saveX, saveY, self.x, self.y, color]

    def writeStringEnd(self):
        if self.curses:
            i = 0
            lineCount = curses.LINES - 15

            offset = int(lineCount/2) - self.reverse[3]
            for line in self.lines:
                if offset + i < 0:
                    i += 1
                    continue
                if i + offset >= lineCount:
                    break
                if i == self.reverse[1]:
                    self.curses.addstr(i + offset, 0, line[:self.reverse[0]], curses.A_NORMAL)
                    if self.reverse[1] == self.reverse[3]:
                        self.curses.addstr(line[self.reverse[0]:self.reverse[2]], curses.A_REVERSE)
                        self.curses.addstr(line[self.reverse[2]:], curses.A_NORMAL)
                    else:
                        self.curses.addstr(line[self.reverse[0]:], curses.A_REVERSE)
                        self.reverse[0] = 0
                        self.reverse[1] += 1
                else:
                    self.curses.addstr(i + offset, 0, line, curses.A_NORMAL)
                i += 1
        else:
            for line in self.lines:
                log.write(line)
