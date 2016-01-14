#!/usr/bin/env python

"""Simple Python CNC transmitter"""

gcode_cheat_sheet = """
    (qv. https://github.com/grbl/grbl/wiki and
         http://linuxcnc.org/docs/2.4/html/gcode_main.html )
    G0 X1 Y2 Z3     -- rapid motion to X/Y/Z
    G1 X1 Y2 Z3     -- feed motion to X/Y/Z
    G2 X1 Y2 I3 J4  -- clockwise arc (I/J = center offset)
    G3 X1 Y2 I3 J4  -- counterclockwise arc (I/J = center offset)
    M0              -- pause program
    M2              -- end program
    F1000           -- set feed rate
"""

import math
import serial
import time

### Gerbil magic

ser = None
# by default this code will only print out the commands, not send
# them to the machine. If you want to run code straight to the
# machine, set this to False - but don't blame me if you smash your
# end mill.
DEBUG = True

def init():
    """Setup the system, flush grbl, etc."""
    # TODO: should we put all the CNC stuff in a class instead?
    if not DEBUG:
        global ser
        ser = serial.Serial(com_port, 9600)
        ser.write("\r\n\r\n")
        time.sleep(2)
        ser.flushInput()

    command("(Initialising...)")
    command("G90")      # mm/min
    command("G17")      # plane to x/y
    command("G21")      # mm units
    command("F500")     # feed at 500mm/min

def is_command(cmd):
    """Is cmd a movement/feed command? ie. not GRBL specific"""
    return cmd[0] in "GMF"

def command(cmd):
    """Send a command to the machine, return result if any."""
    if DEBUG:
        print cmd
        return

    ser.write(cmd.strip() + '\n')
    resp = ser.readline()
    if is_command(cmd):
        if resp.rstrip() != 'ok':
            raise RuntimeError(resp)

    else:
        # handle grbl commands - $$ and friends
        output = [resp]
        resp = ser.readline()
        if resp.rstrip() != 'ok':
            output.append(resp)
        else:
            return output


### config

# all measurements in mm, to 3dp
tool_width = 3.175
step_over = tool_width / 2
step_down = tool_width / 2
safe_height = 10.000
tab_width = tool_width
tab_height = tool_width / 2

#com_port = 'COM11'
com_port = '/dev/ttyACM0'


### grbl setup
# should let the user call this
#init()


### util functions

def frange(start, stop, step):
    """Floating point range."""
    r = start
    if step > 0:
        if start > stop:
            raise ValueError(("Start (%s) should be less than stop (%s),"
                             " for positive values of step (%s)!") % (start, stop, step))
        while r < stop:
            yield r
            r += step

    if step < 0:
        if start < stop:
            raise ValueError(("Start (%s) should be more than stop (%s),"
                             " for negative values of step (%s)!") % (start, stop, step))
        while r > stop:
            yield r
            r += step

    # we'd like to go right up to stop, if there's less than step left
    if abs(r-step - stop) > 0.01:
        yield stop
            
def offset_rect(start, end, offset=None):
    """Offset a rectangle by the toolwidth / 2, so we can do 
       pocketing and profiling more easily."""
    if not offset:
        return (start, end)

    # alter start and end based on the offset (None, 'inside', 'outside')
    min_x = min(start[0], end[0])
    min_y = min(start[1], end[1])
    adj = tool_width / 2
    if offset == 'inside':
        adj = -adj

    # enlarge/ensmall the rectangle by toolwidth / 2 in x and y
    if start[0] == min_x:
        start = (start[0] - adj, start[1])
        end = (end[0] + adj, end[1])
    else:
        start = (start[0] + adj, start[1])
        end = (end[0] - adj, end[1])

    if start[1] == min_y:
        start = (start[0], start[1] - adj)
        end = (end[0], end[1] + adj)
    else:
        start = (start[0], start[1] - adj)
        end = (end[0], end[1] + adj)

    return (start, end)


### Movement functions

# TODO: set alarms for depth, etc. ?
# TODO: bridges on the last pass

def pause():
    """Pause the CNC program? Not sure we need this?"""
    command("M0")

def stop():
    """Stop the program."""
    command("M2")

def comment(message):
    command("(%s)" % message)

def feedrate(rate):
    """Set the feed rate."""
    command("F%d" % rate)


def rapidmove(pos):
    """Move up to safe height, then rapid to pos, then down to z=0."""
    command("G0 Z%.03f" % safe_height)
    command("G0 X%.03f Y%.03f" % pos)
    command("G0 Z0")

def move(pos):
    """Move to pos, at current depth.
    !Dangerous! if you're at the bottom of a hole and you
    try to move somewhere which hasn't been milled yet."""
    command("G1 X%.03f Y%.03f" % pos)

def move_to_safe_height():
    """Used to exit the cut that we've just made.
    Not sure we need this for some things, but it's safer to
    ascend out between cuts."""
    command('G1 Z0')
    command('G0 Z%.03f' % safe_height)


def drill(pos, depth, start_depth=0.0):
    """Drill a hole down to the required depth."""
    rapidmove(pos)
    curr_depth = start_depth
    down_so_far = 0.0
    while curr_depth < depth:
        curr_depth = min(depth, curr_depth+step_down)
        down_so_far += step_down
        command("G1 Z-%.03f" % (curr_depth))
        if down_so_far >= step_down * 5:
            # clear debris - peck, peck!
            # TODO: this can probably be G0, but I'm being careful :)
            command("G1 Z-%.03f" % (curr_depth - step_down * 5))
            #command("G1 Z-%.02f" % (curr_depth)
            down_so_far = 0.0
    move_to_safe_height()


def holdpoints(start, end):
    """Calculate holding tabs based on tab width."""
    # TODO: error if length of start -> end is too short (< tab_width)?
    width = tab_width + tool_width   # add radius at start and end
    
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    
    length = math.sqrt(dx ** 2 + dy ** 2)
    cut_length = (length - width) / 2
    
    cut_x = dx * (cut_length / length) if dx else 0
    cut_y = dy * (cut_length / length) if dy else 0
    
    first_point = (start[0] + cut_x, start[1] + cut_y)
    second_point = (end[0] - cut_x, end[1] - cut_y)
    return (first_point, second_point)


def line_pass(start, end, tab=False):
    """One pass of a line, from start to end. Assumes that we're
    already at target depth, etc.
    If tab is set, use relative coordinates (G91) to go up and down."""
    if not tab:
        move(end)
    else:
        first_point, second_point = holdpoints(start, end)
        move(first_point)
        command("G91")
        command("G1 Z%.03f" % (tab_height))
        command("G90")
        move(second_point)
        command("G91")
        command("G1 Z-%.03f" % (tab_height))
        command("G90")
        move(end)


def line(start, end, depth, start_depth=0.0, tab=False):
    """Line from start to end, traversing back and forth for speed.
    Optionally leave a small tab in the middle on the last pass,
    to hold the part down."""
    rapidmove(start)
    curr_depth = start_depth
    at_start = True
    while curr_depth < depth:
        curr_depth = min(depth, curr_depth+step_down)
        last_pass = (depth - curr_depth < tab_height)
        command("G1 Z-%.03f" % (curr_depth))
        if not (last_pass and tab):
            if at_start:
                move(end)
            else:
                move(start)
        else:
            # we're on the last pass, and need to mill a tab.
            if at_start:
                line_pass(start, end, tab=True)
            else:
                line_pass(end, start, tab=True)

        at_start = not at_start

    move_to_safe_height()


def rectangle(start, end, depth, start_depth=0.0, offset=None, tab=False):
    """Rectangle - start and end are opposite corners.
    This command offsets based on tool width."""
    if offset:
        start, end = offset_rect(start, end, offset)

    #TODO: pull this out to a polygon function? offset will be much
    #      harder with arbitrary polys...
    lines = [
        [(start[0], start[1]), (end[0], start[1])],
        [(end[0], start[1]),   (end[0], end[1])],
        [(end[0], end[1]),     (start[0], end[1])],
        [(start[0], end[1]),   (start[0], start[1])]
    ]
    rapidmove(start)
    curr_depth = start_depth
    while curr_depth < depth:
        curr_depth = min(depth, curr_depth+step_down)
        last_pass = (depth - curr_depth < tab_height)
        command("G1 Z-%.03f" % (curr_depth))
        for start, end in lines:
            if last_pass and tab:
                line_pass(start, end, tab=True)
            else:
                line_pass(start, end)
    move_to_safe_height()


def fillrectangle(start, end, depth, start_depth=0.0, offset=None):
    """Remove everything in the rectangle."""
    if offset:
        start, end = offset_rect(start, end, offset)

    rapidmove(start)
    curr_depth = start_depth

    while curr_depth < depth:
        # calculating x_coords here so that we can go back and forth
        # between start and end on each Z plane and save milling time
        backwards_x = (start[0] > end[0])
        x_coords = list(frange(min(start[0], end[0]),
                               max(start[0], end[0]),
                               step_over))
        if backwards_x:
            x_coords = list(reversed(x_coords))

        # step down
        curr_depth = min(depth, curr_depth+step_down)
        command("G1 Z-%.03f" % (curr_depth))

        back_forth = "forth"
        for x in x_coords:
            if back_forth == "forth":
                move((x, start[1])) # may be a short no-op
                move((x, end[1]))
                back_forth = "back"
            else:
                move((x, end[1])) # may be a short no-op
                move((x, start[1]))
                back_forth = "forth"

        start, end = end, start

    move_to_safe_height()


def dogbone_rect(start, end, depth, start_depth=0.0, sides=None):
    """A 'dogbone' pocket, with corners milled out, so that the edges
    are more-or-less square and you can insert rectangular objects:
     __
    |  |____
    |       
    |   ____
    |__|
    """
    # orientation is X or Y, offset is automatically 'inside'
    # sides is an iterable with any of 'top', 'right', 'bottom', 'left'
    if sides is None:
        sides = []

    start, end = offset_rect(start, end, "inside")
    fillrectangle(start, end, depth, start_depth=start_depth)

    # "normalise" the rectangle, so that start is bottom left.
    start, end = [(min(start[0], end[0]), min(start[1], end[1])),
                  (max(start[0], end[0]), max(start[1], end[1]))]

    # points are already indented tool_width / 2, so we need to
    # 'outdent' by another half a tool_width
    # clockwise
    side_lookup = {
        'top': [
            (start[0], end[1] + tool_width / 2),
            (end[0],   end[1] + tool_width / 2)],
        'right': [
            (end[0] + tool_width / 2, end[1]),
            (end[0] + tool_width / 2, start[1])],
        'bottom': [
            (end[0],   start[1] - tool_width / 2),
            (start[0], start[1] - tool_width / 2)],
        'left': [
            (start[0] - tool_width / 2, start[1]),
            (start[0] - tool_width / 2, end[1])] }
    for side in sides:
        points = side_lookup.get(side, [])
        for point in points:
            drill(point, depth)

    move_to_safe_height()


def point_on_circle(radius, x=None, y=None):
    """Given a circle and one of x or y relative to the centre,
    return the other point. The generated point will be non-negative."""
    if x is None and y is None:
        raise ValueError("Need at least one of x or y!")

    if x is not None:
        theta = math.acos(x / radius)
        y = radius * math.sin(theta)
        return (x, y)

    if y is not None:
        theta = math.asin(y / radius)
        x = radius * math.cos(theta)
        return (x, y)


def tab_up():
    """up tab_height"""
    command("G91")
    command("G1 Z%.03f" % (tab_height))
    command("G90")

def tab_down():
    """down tab_height"""
    command("G91")
    command("G1 Z-%.03f" % (tab_height))
    command("G90")


def circle(centre, radius, depth, start_depth=0.0, offset=None, tab=False):
    """A circle with req. radius"""
    # alter radius based on the offset (None, 'inside', 'outside')
    if offset == 'inside':
        radius -= tool_width / 2
    elif offset == 'outside':
        radius += tool_width / 2
    
    # start at the left hand side of the circle
    start = (centre[0] - radius, centre[1])
    rapidmove(start)
    
    curr_depth = start_depth
    while curr_depth < depth:
        curr_depth = min(depth, curr_depth+step_down)
        last_pass = (depth - curr_depth < tab_height)
        if not (last_pass and tab):
            command("G1 Z-%.03f" % (curr_depth))
            # one pass might work, but the visualiser that I'm using
            # (G-Code Sender) won't show it. So - one pass to the opp.
            # side, and another back
            command("G2 X%.03f Y%.03f I%.03f J0" % (start[0] + 2 * radius, start[1], radius))
            command("G2 X%.03f Y%.03f I-%.03f J0" % (start[0], start[1], radius))
        else:
            # last pass, and we're doing tabs. We pick the easy way,
            # which is to add them to the top, bottom, left and right.
            
            command("G1 Z-%.03f" % (curr_depth))
            
            # mill quarters, less a bit of width equal(ish) to the
            # hold_down width. Going clockwise, so upper left first,
            # then upper right, then lower right then lower left.
            
            # Current implementation is hacky and repetitive, but works ;)
            # Future impl. will use rotate_point on x/y points and I/J
            
            min_d = tab_width + tool_width
            max_d = point_on_circle(radius, x=min_d)[1]
            
            ### upper left
            x = -min_d
            y = max_d
            command("G2 X%.03f Y%.03f I%.03f J0" % (
                        x+centre[0], y+centre[1], radius))
            tab_up()

            # top of circle
            command("G2 X%.03f Y%.03f I%.03f J%.03f" % (
                        centre[0], centre[1]+radius, abs(x), -abs(y)))
            tab_down()

            
            ### upper right
            x = max_d
            y = min_d
            command("G2 X%.03f Y%.03f I0 J-%.03f" % (
                        x+centre[0], y+centre[1], radius))
            tab_up()
            
            # right of circle
            command("G2 X%.03f Y%.03f I%.03f J%.03f" % (
                        centre[0]+radius, centre[1], -abs(x), -abs(y)))
            tab_down()
            
            
            ### lower right
            x = min_d
            y = -max_d
            command("G2 X%.03f Y%.03f I-%.03f J0" % (
                        x+centre[0], y+centre[1], radius))
            tab_up()
            
            # bottom of circle
            command("G2 X%.03f Y%.03f I%.03f J%.03f" % (
                        centre[0], centre[1]-radius, -abs(x), abs(y)))
            tab_down()
            
            
            ### lower left
            x = -max_d
            y = -min_d
            command("G2 X%.03f Y%.03f I0 J%.03f" % (
                        x+centre[0], y+centre[1], radius))
            tab_up()
            
            # left of circle
            command("G2 X%.03f Y%.03f I%.03f J%.03f" % (
                        centre[0]-radius, centre[1], abs(x), abs(y)))
            tab_down()
            
    move_to_safe_height()


def _circle(centre, radius, depth, move_before=False):
    """Very simple circle implementation:
        o doesn't do any moving to safe height.
        o also assumes that it's ok to just move to cutting depth.
    Potentially dangerous, may crash the bit if you're not careful."""
    
    # start at the left hand side of the circle
    start = (centre[0] - radius, centre[1])
    # move to start point if needed. depth_first skips this for speed
    if move_before:
        move(start)
    
    # go to depth, if set
    if depth:
        command("G1 Z-%.03f" % (depth))

    # one pass might work, but the visualiser that I'm using
    # (G-Code Sender) won't show it. So - one pass to the opp.
    # side, and another back
    command("G2 X%.03f Y%.03f I%.03f J0" % (start[0] + 2*radius, start[1], radius))
    command("G2 X%.03f Y%.03f I-%.03f J0" % (start[0], start[1], radius))


def fillcircle(centre, radius, depth, start_depth=0.0, depth_first=True):
    """Completely mill out a circle.

    depth_first=True: Start with a minimum circle at the centre, and work outwards.
               =False: mill whole circle one step deep, then the rest.
    """
    rapidmove((centre[0]-step_over, centre[1]))
    
    # offset is automatically considered to be 'inside'.
    radius -= tool_width / 2
    
    # build a list of depth + x-radius values
    # These need to be lists, since we iterate over them multiple times.
    depths = list(frange(start_depth+step_down, depth, step_down))
    x_starts = list(frange(centre[0], centre[0] - radius, -step_over))
    
    if depth_first:
        points = [[(x, d) for d in depths] for x in x_starts]
    else:
        points = [[(x, d) for x in x_starts] for d in depths]
    
    for each_pass in points:
        move((each_pass[0][0], centre[1]))
        if not depth_first:
            # all circles in breadth_first are the same height
            command("G1 Z-%0.3f" % each_pass[0][1])
            
        for each_xstart, each_depth in each_pass:
            if depth_first:
                _circle(centre, centre[0]-each_xstart, each_depth, move_before=False)
            else:
                _circle(centre, centre[0]-each_xstart, depth=None, move_before=True)
        
        if depth_first:
            # move back up before next pass to the outside
            command("G1 Z0.100")

    move_to_safe_height()

