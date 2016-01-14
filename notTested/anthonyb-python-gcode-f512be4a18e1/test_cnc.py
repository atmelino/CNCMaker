#!/usr/bin/env/python

import cnc
import math


# test utilities
def assert_fequal(a, b, precision=0.001):
    assert abs(a - b) < precision, \
        "%s and %s are not equal!" % (a, b)

def fequal(a, b, precision=0.0001):
    return abs(a - b) < precision

def assert_lequal(a, b, precision=0.001):
    assert (len(a) == len(b) and
        all(fequal(a, b, precision) for a, b in zip(a,b))), \
        "%s and %s are not equal!" % (a, b)


# mock out the command function so that it's easily testable
command_list = []
def mock_command(cmd):
    command_list.append(cmd.rstrip())
cnc.command = mock_command

def command_list_reset():
    global command_list
    command_list = []
cnc.DEBUG = False


# set some easy to read parameters
cnc.tool_width = 1.000
cnc.step_over = 1.000
cnc.step_down = 1.000
cnc.safe_height = 5.000
cnc.tab_width = 1.000
cnc.tab_height = 1.000

### test utils
def test_frange():
    assert_lequal(
       list(cnc.frange(0.000, 1.000, 0.1)),
       [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])

    #reversed doesn't work!
    assert_lequal(
       list(cnc.frange(1.000, 0.000, -0.1)),
       list(reversed([0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])))

    assert_lequal(
       list(cnc.frange(-1.000, 0.000, 0.1)),
       [-1.0, -0.9, -0.8, -0.7, -0.6, -0.5, -0.4, -0.3, -0.2, -0.1, 0.0])

def test_offset_rect():
    assert cnc.offset_rect((1,1), (3,3), None) == ((1,1), (3,3))
    assert cnc.offset_rect((1,1), (3,3), "inside") == ((1.5,1.5), (2.5,2.5))
    assert cnc.offset_rect((1,1), (3,3), "outside") == ((0.5,0.5), (3.5,3.5))


### test movement commands
def test_rapidmove():
    command_list_reset()
    cnc.rapidmove((1,1))
    print command_list
    assert command_list == ['G0 Z5.000', 'G0 X1.000 Y1.000', 'G0 Z0']

def test_move():
    command_list_reset()
    cnc.move((2,2))
    print command_list
    assert command_list == ['G1 X2.000 Y2.000']

def test_drill():
    command_list_reset()
    cnc.drill((5,5), 3)
    print command_list
    assert command_list == [
        'G0 Z5.000', 'G0 X5.000 Y5.000', 'G0 Z0',
        'G1 Z-1.000', 'G1 Z-2.000', 'G1 Z-3.000',
        'G1 Z0', 'G0 Z5.000']

def test_peck_drill():
    """Drilling more than step_down * 5 should trigger a peck."""
    command_list_reset()
    cnc.drill((5,5), 6)
    print command_list
    assert command_list == [
        'G0 Z5.000', 'G0 X5.000 Y5.000', 'G0 Z0', 
        'G1 Z-1.000', 'G1 Z-2.000', 'G1 Z-3.000', 'G1 Z-4.000', 
        'G1 Z-5.000', 'G1 Z-0.000', 'G1 Z-6.000', 
        'G1 Z0', 'G0 Z5.000']

def test_line():
    command_list_reset()
    cnc.line((1,1), (5,5), 2)
    print command_list
    assert command_list == [
        'G0 Z5.000', 'G0 X1.000 Y1.000', 'G0 Z0', 
        'G1 Z-1.000', 'G1 X5.000 Y5.000',
        'G1 Z-2.000', 'G1 X1.000 Y1.000',
        'G1 Z0', 'G0 Z5.000']


def test_rectangle_noprofile():
    command_list_reset()
    cnc.rectangle((1,1), (5, 5), 2, offset=None)
    print command_list
    assert command_list == [
        'G0 Z5.000', 'G0 X1.000 Y1.000', 'G0 Z0', 
        'G1 Z-1.000', 
        'G1 X5.000 Y1.000', 'G1 X5.000 Y5.000', 
        'G1 X1.000 Y5.000', 'G1 X1.000 Y1.000', 
        'G1 Z-2.000', 
        'G1 X5.000 Y1.000', 'G1 X5.000 Y5.000', 
        'G1 X1.000 Y5.000', 'G1 X1.000 Y1.000', 
        'G1 Z0', 'G0 Z5.000']

def test_rectangle_outside():
    command_list_reset()
    cnc.rectangle((1,1), (5, 5), 2, offset="outside")
    print command_list
    assert command_list == [
        'G0 Z5.000', 'G0 X0.500 Y0.500', 'G0 Z0', 
        'G1 Z-1.000', 
        'G1 X5.500 Y0.500', 'G1 X5.500 Y5.500', 
        'G1 X0.500 Y5.500', 'G1 X0.500 Y0.500', 
        'G1 Z-2.000', 
        'G1 X5.500 Y0.500', 'G1 X5.500 Y5.500', 
        'G1 X0.500 Y5.500', 'G1 X0.500 Y0.500', 
        'G1 Z0', 'G0 Z5.000']

def test_rectangle_inside():
    command_list_reset()
    cnc.rectangle((1,1), (5, 5), 2, offset="inside")
    print command_list
    assert command_list == [
        'G0 Z5.000', 'G0 X1.500 Y1.500', 'G0 Z0',
        'G1 Z-1.000',
        'G1 X4.500 Y1.500', 'G1 X4.500 Y4.500', 
        'G1 X1.500 Y4.500', 'G1 X1.500 Y1.500', 
        'G1 Z-2.000', 
        'G1 X4.500 Y1.500', 'G1 X4.500 Y4.500', 
        'G1 X1.500 Y4.500', 'G1 X1.500 Y1.500', 
        'G1 Z0', 'G0 Z5.000']


def test_rectangle_startdepth():
    command_list_reset()
    cnc.rectangle((1,1), (5, 5), 5, start_depth=3, offset="inside")
    print command_list
    assert command_list == [
        'G0 Z5.000', 'G0 X1.500 Y1.500', 'G0 Z0', 
        'G1 Z-4.000', 
        'G1 X4.500 Y1.500', 'G1 X4.500 Y4.500', 
        'G1 X1.500 Y4.500', 'G1 X1.500 Y1.500', 
        'G1 Z-5.000', 
        'G1 X4.500 Y1.500', 'G1 X4.500 Y4.500', 
        'G1 X1.500 Y4.500', 'G1 X1.500 Y1.500', 
        'G1 Z0', 'G0 Z5.000']

def test_fillrectangle():
    command_list_reset()
    cnc.fillrectangle((1,1), (5.5, 5.5), 3, offset="inside")
    print command_list
    assert command_list == [
        'G0 Z5.000', 'G0 X1.500 Y1.500', 'G0 Z0', 
        'G1 Z-1.000', 
        'G1 X1.500 Y1.500', 'G1 X1.500 Y5.000', 
        'G1 X2.500 Y5.000', 'G1 X2.500 Y1.500', 
        'G1 X3.500 Y1.500', 'G1 X3.500 Y5.000', 
        'G1 X4.500 Y5.000', 'G1 X4.500 Y1.500', 
        'G1 X5.000 Y1.500', 'G1 X5.000 Y5.000', 
        'G1 Z-2.000', 
        'G1 X5.000 Y5.000', 'G1 X5.000 Y1.500', 
        'G1 X4.500 Y1.500', 'G1 X4.500 Y5.000', 
        'G1 X3.500 Y5.000', 'G1 X3.500 Y1.500', 
        'G1 X2.500 Y1.500', 'G1 X2.500 Y5.000', 
        'G1 X1.500 Y5.000', 'G1 X1.500 Y1.500', 
        'G1 Z-3.000', 
        'G1 X1.500 Y1.500', 'G1 X1.500 Y5.000', 
        'G1 X2.500 Y5.000', 'G1 X2.500 Y1.500', 
        'G1 X3.500 Y1.500', 'G1 X3.500 Y5.000', 
        'G1 X4.500 Y5.000', 'G1 X4.500 Y1.500', 
        'G1 X5.000 Y1.500', 'G1 X5.000 Y5.000', 
        'G1 Z0', 'G0 Z5.000']


def test_dogbone():
    command_list_reset()
    cnc.dogbone_rect((1,1), (4,5), 1, 
                     sides=["top", "right", "bottom", "left"])
    print command_list
    assert command_list == [
        'G0 Z5.000', 'G0 X1.500 Y1.500', 'G0 Z0',
        'G1 Z-1.000', 
        'G1 X1.500 Y1.500', 'G1 X1.500 Y4.500', 'G1 X2.500 Y4.500', 
        'G1 X2.500 Y1.500', 'G1 X3.500 Y1.500', 'G1 X3.500 Y4.500', 
        'G1 Z0', 'G0 Z5.000', 

        # top pockets
        'G0 Z5.000', 'G0 X1.500 Y5.000', 'G0 Z0', 'G1 Z-1.000', 
        'G1 Z0', 'G0 Z5.000', 

        'G0 Z5.000', 'G0 X3.500 Y5.000', 'G0 Z0', 'G1 Z-1.000', 
        'G1 Z0', 'G0 Z5.000', 

        # right pockets
        'G0 Z5.000', 'G0 X4.000 Y4.500', 'G0 Z0', 'G1 Z-1.000', 
        'G1 Z0', 'G0 Z5.000', 

        'G0 Z5.000', 'G0 X4.000 Y1.500', 'G0 Z0', 'G1 Z-1.000', 
        'G1 Z0', 'G0 Z5.000', 

        # bottom pockets
        'G0 Z5.000', 'G0 X3.500 Y1.000', 'G0 Z0', 'G1 Z-1.000',
        'G1 Z0', 'G0 Z5.000', 

        'G0 Z5.000', 'G0 X1.500 Y1.000', 'G0 Z0', 'G1 Z-1.000', 
        'G1 Z0', 'G0 Z5.000', 

        # left pockets
        'G0 Z5.000', 'G0 X1.000 Y1.500', 'G0 Z0', 'G1 Z-1.000', 
        'G1 Z0', 'G0 Z5.000', 

        'G0 Z5.000', 'G0 X1.000 Y4.500', 'G0 Z0', 'G1 Z-1.000',
        'G1 Z0', 'G0 Z5.000', 

        'G1 Z0', 'G0 Z5.000']


def test_dogbone_topbottom():
    command_list_reset()
    cnc.dogbone_rect((1,1), (4,5), 1, sides=["bottom", "top"])
    print command_list
    assert command_list == [
        'G0 Z5.000', 'G0 X1.500 Y1.500', 'G0 Z0',
        'G1 Z-1.000', 
        'G1 X1.500 Y1.500', 'G1 X1.500 Y4.500', 'G1 X2.500 Y4.500', 
        'G1 X2.500 Y1.500', 'G1 X3.500 Y1.500', 'G1 X3.500 Y4.500', 
        'G1 Z0', 'G0 Z5.000', 

        # bottom pockets
        'G0 Z5.000', 'G0 X3.500 Y1.000', 'G0 Z0', 'G1 Z-1.000',
        'G1 Z0', 'G0 Z5.000', 

        'G0 Z5.000', 'G0 X1.500 Y1.000', 'G0 Z0', 'G1 Z-1.000', 
        'G1 Z0', 'G0 Z5.000', 

        # top pockets
        'G0 Z5.000', 'G0 X1.500 Y5.000', 'G0 Z0', 'G1 Z-1.000', 
        'G1 Z0', 'G0 Z5.000', 

        'G0 Z5.000', 'G0 X3.500 Y5.000', 'G0 Z0', 'G1 Z-1.000', 
        'G1 Z0', 'G0 Z5.000', 

        'G1 Z0', 'G0 Z5.000']


def test_holdpoints():
    assert cnc.holdpoints((1,1), (6,1)) == ((2.5, 1), (4.5, 1))
    assert cnc.holdpoints((6,1), (1,1)) == ((4.5, 1), (2.5, 1))
    
    assert cnc.holdpoints((1,1), (1,6)) == ((1, 2.5), (1, 4.5))
    assert cnc.holdpoints((1,6), (1,1)) == ((1, 4.5), (1, 2.5))

    result = cnc.holdpoints((0,0), (4,3))
    assert_lequal(result[0], (1.2, 0.9))
    assert_lequal(result[1], (2.8, 2.1))
    
    result = cnc.holdpoints((0,0), (-10, 5))
    assert_lequal(result[0], (-4.106, 2.053))
    assert_lequal(result[1], (-5.894, 2.947))


def test_holddown_line():
    command_list_reset()
    cnc.line((0,0), (10,10), 2, tab=True)
    print command_list
    assert command_list == [
        'G0 Z5.000', 'G0 X0.000 Y0.000', 'G0 Z0', 
        'G1 Z-1.000', 'G1 X10.000 Y10.000', 
        'G1 Z-2.000', 'G1 X5.707 Y5.707', 
        'G91', 'G1 Z1.000', 'G90', 'G1 X4.293 Y4.293', 
        'G91', 'G1 Z-1.000', 'G90', 'G1 X0.000 Y0.000',
        'G1 Z0', 'G0 Z5.000']

def test_multi_holddown_line():
    """If the tab_height is greater than the pass height,
    we should get multiple tab passes."""
    command_list_reset()
    cnc.tab_height = 1.5
    cnc.line((0,0), (10,10), 3, tab=True)
    print command_list
    assert command_list == [
        'G0 Z5.000', 'G0 X0.000 Y0.000', 'G0 Z0', 
        'G1 Z-1.000', 'G1 X10.000 Y10.000', 
        'G1 Z-2.000', 
        'G1 X5.707 Y5.707', 'G91', 'G1 Z1.500', 'G90',
        'G1 X4.293 Y4.293', 'G91', 'G1 Z-1.500', 'G90',
        'G1 X0.000 Y0.000', 
        'G1 Z-3.000', 
        'G1 X4.293 Y4.293', 'G91', 'G1 Z1.500', 'G90', 
        'G1 X5.707 Y5.707', 'G91', 'G1 Z-1.500', 'G90', 
        'G1 X10.000 Y10.000', 
        'G1 Z0', 'G0 Z5.000']
    cnc.tab_height = 1.0

def test_holddown_rectangle():
    command_list_reset()
    cnc.rectangle((1,1), (10, 10), 3, offset="outside", tab=True)
    print command_list
    assert command_list == [
        'G0 Z5.000', 'G0 X0.500 Y0.500', 'G0 Z0', 
        'G1 Z-1.000', 
        'G1 X10.500 Y0.500', 'G1 X10.500 Y10.500', 
        'G1 X0.500 Y10.500', 'G1 X0.500 Y0.500', 
        'G1 Z-2.000', 
        'G1 X10.500 Y0.500', 'G1 X10.500 Y10.500', 
        'G1 X0.500 Y10.500', 'G1 X0.500 Y0.500', 
        'G1 Z-3.000', 
        'G1 X4.500 Y0.500', 'G91', 'G1 Z1.000', 'G90', 
        'G1 X6.500 Y0.500', 'G91', 'G1 Z-1.000', 'G90', 
        'G1 X10.500 Y0.500', 
        'G1 X10.500 Y4.500', 'G91', 'G1 Z1.000', 'G90', 
        'G1 X10.500 Y6.500', 'G91', 'G1 Z-1.000', 'G90', 
        'G1 X10.500 Y10.500', 
        'G1 X6.500 Y10.500', 'G91', 'G1 Z1.000', 'G90', 
        'G1 X4.500 Y10.500', 'G91', 'G1 Z-1.000', 'G90', 
        'G1 X0.500 Y10.500', 
        'G1 X0.500 Y6.500', 'G91', 'G1 Z1.000', 'G90', 
        'G1 X0.500 Y4.500', 'G91', 'G1 Z-1.000', 'G90', 
        'G1 X0.500 Y0.500', 
        'G1 Z0', 'G0 Z5.000']


def test_point_on_circle():
    pi_4 = math.pi / 4
    qtr_c = math.sin(pi_4)
    
    expected = [
        (10.0, 0.0, 10.0),
        (10.0, 10.0, 0.0),

        # -ve x and y: will come out +ve
        (10.0, -10.0, 0.0),
        (10.0, 0.0, -10.0),
        
        # 45 degrees
        (10.0, 10.0 * qtr_c, 10.0 * qtr_c),
        
        # real world
        (50.0, 5.003, 49.749),
    ]
    for radius, x, y in expected:
        assert_fequal(cnc.point_on_circle(radius, x, None)[1], abs(y))
        assert_fequal(cnc.point_on_circle(radius, None, y)[0], abs(x))
        assert_fequal(math.sqrt(x**2 + y**2), radius)


