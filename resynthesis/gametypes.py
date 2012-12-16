import logging

from resynthesis import *

class DanceSingle(object):
    # Constants
    L, D, U, R = xrange(4)
    # Attributes
    l = L
    r = R
    h1 = -1
    h2 = -1
    last_used = 'j'
    jack = False
    
    def __init__(self):
        self.log = logging.getLogger('synctools')
    
    def _is_hold(self, f):
        # Includes rolls because they're basically the same for our purposes
        return f in (4, 5, 6, 7, 12, 13, 14, 15)
    
    def _is_roll(self, f):
        return f >= 12
    
    def _is_tail(self, f):
        return 8 <= f < 12
    
    def tap(self, arrow):
        self.jack = False
        panel = arrow % 4
        # Hands
        if self._is_hold(self.r) and self._is_hold(self.l):
            # Three holds and a tap
            if self._is_hold(self.h1):
                self.h2 = arrow
            # Two holds and a tap
            else:
                self.h1 = arrow
                self.h2 = -1
            last_used = 'h'
        # TODO: lots of repeated code here, but reducing repetition would also
        #       reduce readability... sigh
        # Last used left foot
        elif self.last_used == 'l':
            # One-footing or jack
            if self._is_hold(self.r) or self.l == panel:
                self.l = arrow
                self.jack = True
            # Crossover or double-step (always assume double-step)
            elif arrow == self.L:
                if self._is_hold(self.l):
                    self.r = arrow
                    self.last_used = 'r'
                else:
                    self.log.warn("Double step")
                    self.l = arrow
            # Alternating feet
            else:
                self.r = arrow
                self.last_used = 'r'
        # Last used right foot
        elif self.last_used == 'r':
            # One-footing or jack
            if self._is_hold(self.l) or self.r == panel:
                self.r = arrow
                self.jack = True
            # Crossover or double-step (always assume double-step)
            elif arrow == self.R:
                if self._is_hold(self.r):
                    self.l = arrow
                    self.last_used = 'l'
                else:
                    self.log.warn("Double step")
                    self.r = arrow
            # Alternating feet
            else:
                self.l = arrow
                self.last_used = 'l'
        # Last used both (jump)
        elif self.last_used == 'j':
            # One hold
            if self._is_hold(self.l):
                self.r = arrow
                self.last_used = 'r'
            elif self._is_hold(self.r):
                self.l = arrow
                self.last_used = 'l'
            # Unambiguous
            elif self.l == panel or self.L == panel:
                self.l = arrow
                self.last_used = 'l'
            elif self.r == panel or self.R == panel:
                self.r = arrow
                self.last_used = 'r'
            # Ambiguous
            elif (self.l == self.L and self.r == self.U and panel == self.D or
                  self.l == self.L and self.r == self.D and panel == self.U):
                self.log.warn("Semi-ambiguous tap")
                self.l = arrow
                self.last_used = 'l'
            elif (self.r == self.R and self.l == self.U and panel == self.D or
                  self.r == self.R and self.l == self.D and panel == self.U):
                self.log.warn("Semi-ambiguous tap")
                self.r = arrow
                self.last_used = 'r'
            # Completely ambiguous (i.e. LR jump followed by U/D tap)
            else:
                self.log.warn("Ambiguous tap")
                # Arbitrary values
                self.l = arrow
                self.last_used = 'l'
    
    def hold(self, arrow):
        self.tap(arrow + 4)
    
    def roll(self, arrow):
        self.tap(arrow + 12)
    
    def tail(self, arrow):
        self.jack = False
        # Left tail
        if self.l / 4 in (1, 3) and self.l % 4 == arrow:
            self.l = self.l % 4 + 8
            self.last_used = 'l'
        # Right tail
        elif self.r / 4 in (1, 3) and self.r % 4 == arrow:
            self.r = self.r % 4 + 8
            self.last_used = 'r'
        # Hold wasn't found
        else:
            self.log.warn("Unmatched tail")
    
    def jump(self, arrow1, arrow2):
        self.jack = False
        panel1 = arrow1 % 4
        panel2 = arrow2 % 4
        # Hands (probably actually bracketing but oh well)
        if self._is_hold(self.r) or self._is_hold(self.l):
            self.h1 = arrow1
            self.h2 = arrow2
            self.last_used = 'h'
            return
        # Both feet were just used to hit these arrows
        if (self.l == panel1 and self.r == panel2 or
                self.l == panel2 and self.r == panel1):
            self.jack = True
        # At least one foot was just used to hit one of these arrows
        if self.l == panel1 or self.r == panel2:
            self.l = arrow1
            self.r = arrow2
        elif self.l == panel2 or self.r == panel1:
            self.l = arrow2
            self.r = arrow1
        # At least one arrow is non-ambiguous
        elif self.L == panel1 or self.R == panel2:
            self.l = arrow1
            self.r = arrow2
        elif self.L == panel2 or self.R == panel1:
            self.l = arrow2
            self.r = arrow1
        # Ambiguous U/D jump
        else:
            self.log.warn("Ambiguous jump")
            # Arbitrary values
            self.l = arrow1
            self.r = arrow2
        self.last_used = 'j'
    
    def state(self, readable=False):
        l = r = ''
        # Left tail
        if self._is_tail(self.l):
            l = 'tail'
            self.l %= 4
            # Immediately following right event
            if self.last_used == 'r':
                if self._is_hold(self.r):
                    if self._is_roll(self.r):
                        r = 'roll'
                    else:
                        r = 'hold'
                elif self._is_tail(self.r):
                    r = 'tail'
                    self.last_used = 'j'
                else:
                    r = 'tap'
        # Right tail
        elif self._is_tail(self.r):
            r = 'tail'
            self.r %= 4
            # Immediately following left event
            if self.last_used == 'l':
                if self._is_hold(self.l):
                    if self._is_roll(self.l):
                        l = 'roll'
                    else:
                        l = 'hold'
                elif self._is_tail(self.l):
                    l = 'tail'
                    self.last_used = 'j'
                else:
                    l = 'tap'
        elif self.last_used == 'j':
            l = 'tap'
            r = 'tap'
        elif self.last_used == 'r':
            r = 'tap'
        elif self.last_used == 'l':
            l = 'tap'
        if self._is_hold(self.l):
            if self._is_roll(self.l):
                l = 'roll'
            else:
                l = 'hold'
        if self._is_hold(self.r):
            if self._is_roll(self.r):
                r = 'roll'
            else:
                r = 'hold'
        if readable:
            return '%s %s' % (self.STATES[l], self.STATES[r])
        return ResynthesisState(l, r, self.h1, self.h2)
        
    def parse_row(self, row):
        # No taps
        if set(row) == set('0'):
            return
        # Single tap, hold, roll, or tail
        if row.count('0') == 3:
            if '1' in row:
                self.tap(row.find('1'))
            elif '2' in row:
                self.hold(row.find('2'))
            elif '3' in row:
                self.tail(row.find('3'))
            elif '4' in row:
                self.roll(row.find('4'))
        # Jump with no tails
        elif row.count('0') == 2 and '3' not in row:
            arrows = []
            for i, col in enumerate(row):
                if col != '0':
                    arrows.append(i + 4 * (int(col) - 1))
            self.jump(*arrows)
        # Tail and one or two taps / other tails
        elif '0' in row and '3' in row:
            arrows = []
            for i, col in enumerate(row):
                if col == '3':
                    self.tail(i)
                elif col != '0':
                    arrows.append(i + 4 * (int(col) - 1))
            if len(arrows) == 1:
                self.tap(arrows[0])
            elif len(arrows) == 2:
                self.jump(*arrows)
        else:
            raise ResynthesisError()
        return self.state()