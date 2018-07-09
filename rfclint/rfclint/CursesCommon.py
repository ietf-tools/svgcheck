try:
    import curses
    haveCurses = True
except ImportError:
    haveCurses = False

from rfctools_common import log



class CursesCommon(object):
    def __init__(self, config):
        self.no_curses = False
        self.curses = None
        
        self.interactive = False

        if config.options.output_filename is not None:
            self.interactive = True

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
                    log.error("Problem loading curses - " + tostr(e))
            else:
                log.warn("Unable to load CURSES for python")


    def endwin(self):
        if self.curses:
            try:
                curses.nocbreak()
                curses.echo()
                curses.endwin()
            except curses.error as e:
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
            if self.x != 0 and line[-1] != ' ' and not partialString:
                self.lines[-1] += " "
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
                    break;
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
