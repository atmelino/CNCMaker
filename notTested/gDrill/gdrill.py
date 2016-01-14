# gDrill v1.1

# Copyright (c) 2013 Derek Hugger

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


# WARNING!!!!! WARNING!!!!! WARNING!!!!! WARNING!!!!! WARNING!!!!! WARNING!!!!!
# Neither this script nor its G-Code outputs have been fully tested. Use them at your own risk.



# CNC routers are great for cutting parts, but their ability to cut small, interpolated holes is not always sufficient.
# Interpolating a hole on a CNC router can lead to an inaccurately sized hole or a hole that is elliptical in shape.
# This program allows a user to mount a small drill bit or end mill into a CNC router and drill a tiny pilot hole at each desired hole location.
# Once these pilot holes are drilled, parts (minus their holes) can be cut out as they would be normally.
# Once the parts are cut, a drill press can be used to accurately drill the pilot holes to their correct sizes.

# This program uses a text file as an input to generate hole-drilling G-Code that can drive any G-Code capable CNC router.
# The text file must have certain parameters (listed below in the intro function) and any number of hole coordinates to drill.

# PLEASE NOTE: After the G-Code file is generated, a plot of all the coordinates is printed on screen. This plot is for visual reference only.
# The plot function was built for the fun of it (<--- nerd!). The math in this function has not been fully tested, so expect inaccuracies and expect that points may be missing.
# The good news is the plot does not affect the G-Code file. The G-Code file is generated entirely from the inputted .txt file, with no influence at all from the plot.


def intro():		# This function displays an introduction to the program and gives some basic formatting instructions.
	print'''This program uses a .txt file to generate G-Code to drill pilot holes at given (x,y) coordinates.
The .txt file must be formatted as follows:

                         example:  -----------------
Units (in or mm)                   | in            |
Retract Height                     | 0.1           |
Hole Depth                         | 0.50          |
Depth per Plunge                   | 0.10          |
Feed Rate                          | 10            |
                                   |               |
X (hole 1)                         | 1.235         |
Y (hole 1)                         | 6.378         |
                                   |               |
X (hole 2)                         | -1.590        |
Y (hole 2)                         | 5.722         |
                                   |               |
X (hole 3)                         | 4.699         |
Y (hole 3)                         | 3.824         |
                                   -----------------
								   
A blank line must be used after the five drilling parameters and between each set of coordinates.
There is no limit to the number of coordinates to be drilled.
If Depth Per Plunge >= Hole Depth, holes will be drilled with a single plunge.'''
	
	
def plunge_once (depth, f_rate, i, output_file):								# This function is called when the Hole Depth is less than or equal to Depth per Plunge (one plunge per hole).
	output_file.write('G1Z-%.3fF%.3f (plunge %d)\n' % (depth, f_rate, (i+2)/2))	# Writes the G-code plunge command.

	
def plunge_mult (depth, depth_per, f_rate, i, output_file):						# This function is called when the Hole Depth is greater than Depth per Plunge (multiple plunges per hole).
	p_count = 1				# Plunge count
	p_depth = depth_per 	# p_depth increments after each plunge. This command sets its starting depth.
	while p_depth < depth:	# This loop incrementally writes plunge commands, increasing plunge the depth until the final depth is reached.
		output_file.write('G1Z-%.3fF%.3f (hole %d, plunge %d)\n' % (p_depth, f_rate, (i+2)/2, p_count))
		output_file.write('G0Z0.000 (retract to clean)\n')
		p_depth += depth_per
		p_count += 1
	output_file.write('G1Z-%.3fF%.3f (hole %d, plunge %d)\n' % (depth, f_rate, (i+2)/2, p_count))	# writes the final depth plunge command

	
def format_check (input_file_name): # This function checks to make sure the input file is formatted correctly.
	# Error Codes (ecode): 1. Units  2. Parameters  3. Blank line missing between parameters and coordinates. 4. Coordinate formatting error. 
	ecode = 0
	input_file = open(input_file_name)
	while True:								# This first section checks the formatting of the parameters.
		test = input_file.readline()
		test = test.strip()					# .strip removes the "\n" in the inputted string.
		if test != ('in' or 'mm'):			# Makes sure the first line of the input file defines units properly.
			ecode = 1
			break
		for tester in range(0,4):
			test = input_file.readline()
			test = test.strip()
			try: (float(test))				# Verifies that the second 4 lines of code are real numbers.
			except ValueError:
				ecode = 2
			if (len(test) < 1):
				ecode = 2
		if ecode != 0: break
		test = input_file.readline()
		test = test.strip()
		if len(test) != 0:					# Verifies that there is a blank line between the drilling parameters and the first coordinate.
			ecode = 3
			break
		while True:							# This section repeats as needed, checking the formatting of each set of coordinates; two lines of real numbers then a blank line.
			for tester in range(0,2):
				test = input_file.readline()
				if len(test.strip()) == 0:
					ecode = 4
					break
				if len(test) == 0:
					ecode = 4
					break
				test = test.strip()
				try: (float(test))
				except ValueError:
					ecode = 4
					break
			if ecode != 0:
				break				
			test = input_file.readline()
			if len(test) == 0:
				ecode = 0
				break 						# The loop breaks here once the end of file is reached.
			elif len(test.strip()) != 0:	
					ecode = 4
					break		
		break								# Once the coordinate check loop breaks, the loop that it is nested into breaks as well. 
	input_file.close
	return ecode							# The function returns an error code that is used to determine whether a G-Code file can be created. 

	
def plot (xmin,xmax,ymin,ymax,coord_list):	#This function creates a plot of the coordinates. THIS PLOT IS FOR VISUAL REFERENCES ONLY. It has not been fully tested for accuracy.
	print "\n\n"	
	# range_x and range_y definitions: 	0 = all values positive		1 = all values negative		2 = mixed values (positive and negative)
	if xmin >= 0 and xmax >= 0:
		range_x = 0					# all x values positive
	elif xmin <= 0 and xmax <= 0:
		range_x = 1					# all x values negative
	else:
		range_x = 2					# x values mixed

	if ymin >= 0 and ymax >= 0:
		range_y = 0					# all y values positive
	elif ymin <= 0 and ymax <= 0:
		range_y = 1					# all y values negative
	else:
		range_y = 2					# y values mixed
		
	xplot = 50		# This is the widest (in number of characters) the plot will be.
	yplot = 30		# This is the tallest (in number of characters) the plot will be.

	# The following (giant) if statment determines how the plot scales, depending on where the coordinates are in which quadrant(s).
	# It essentially determines which quadrants are needed, and whether the max x value is greater than the max y value (or vise versa), and scales the graph accordingly.
	if range_x == 0 and range_y == 0 and xmax >= ymax:				# all values positive, x is greater
		x_plot_max = xplot
		y_plot_max = int(yplot * ymax/xmax)
		x_plot_min = 0
		y_plot_min = 0
	elif range_x == 0 and range_y == 0 and ymax > xmax: 			# all values positive, y is greater
		x_plot_max = int(xplot * xmax/ymax)
		y_plot_max = yplot
		x_plot_min = 0
		y_plot_min = 0
	elif range_x == 1 and range_y == 0 and abs(xmin) >= ymax:		# x values negative, y values positive, x is greater
		x_plot_max = 0
		y_plot_max = int(yplot * ymax/abs(xmin))
		x_plot_min = -xplot
		y_plot_min = 0
	elif range_x == 1 and range_y == 0 and abs(xmin) < ymax:		# x values negative, y values positive, y is greater
		x_plot_max = 0
		y_plot_max = yplot
		x_plot_min = -int(xplot * abs(xmin)/ymax)
		y_plot_min = 0
	elif range_x == 0 and range_y == 1 and xmax >= abs(ymin):		# x values positive, y values negative, x is greater
		x_plot_max = xplot
		y_plot_max = 0
		x_plot_min = 0
		y_plot_min = -int(yplot * abs(ymin)/xmax)
	elif range_x == 0 and range_y == 1 and xmax < abs(ymin):		# x values positive, y values negative, y is greater
		x_plot_max = int(xplot * xmax/abs(ymin))
		y_plot_max = 0
		x_plot_min = 0
		y_plot_min = -yplot	
	elif range_x == 1 and range_y == 1 and xmin <= ymin:			#all values are negative, x is greater
		x_plot_max = 0
		y_plot_max = 0
		x_plot_min = -xplot
		y_plot_min = -int(yplot * ymin/xmin)
	elif range_x == 1 and range_y == 1 and xmin > ymin:				# all values are negative, y is greater
		x_plot_max = 0
		y_plot_max = 0
		x_plot_min = -int(xplot * xmin/ymin)
		y_plot_min = -yplot			
	elif range_x == 2 and range_y == 0 and abs(xmax-xmin) >= ymax:	# x values mixed, y values positive, x is greater
		x_plot_max = int(xplot * (xmax/(xmax-xmin)))
		y_plot_max = int(yplot * ymax/abs(xmax-xmin))
		x_plot_min = int(xplot * (xmin/(xmax-xmin)))
		y_plot_min = 0
	elif range_x == 2 and range_y == 0 and abs(xmax-xmin) < ymax:	# x values mixed, y values positive, y is greater
		x_plot_max = int(xplot * xmax/ymax)
		y_plot_max = yplot
		x_plot_min = int(xplot * xmin/ymax)
		y_plot_min = 0	
	elif range_x == 2 and range_y == 1 and abs(xmax-xmin) >= abs(ymin):	# x values mixed, y values negative, x is greater
		x_plot_max = int(xplot * (xmax/(xmax-xmin)))
		y_plot_max = 0
		x_plot_min = int(xplot * (xmin/(xmax-xmin)))
		y_plot_min = int(yplot * ymin/abs(xmax-xmin))
	elif range_x == 2 and range_y == 1 and abs(xmax-xmin) < abs(ymin):	# x values mixed, y values negative, y is greater
		x_plot_max = -int(xplot * xmax/ymin)
		y_plot_max = 0
		x_plot_min = -int(xplot * xmin/ymin)
		y_plot_min = -yplot		
	elif range_x == 0 and range_y == 2 and xmax >= abs(ymax-ymin):		# x values positive, y values mixed, x is greater
		x_plot_max = xplot
		y_plot_max = int(yplot * ymax/xmax)
		x_plot_min = 0
		y_plot_min = int(yplot * ymin/xmax)
	elif range_x == 0 and range_y == 2 and xmax < abs(ymax-ymin):		# x values positive, y values mixed, y is greater
		x_plot_max = int(xplot * xmax/abs(ymax-ymin))
		y_plot_max = int(yplot * (ymax/(ymax-ymin)))
		x_plot_min = 0
		y_plot_min = int(yplot * (ymin/(ymax-ymin)))	
	elif range_x == 1 and range_y == 2 and abs(xmin) >= abs(ymax-ymin):	# x values negative, y values mixed, x is greater
		x_plot_max = 0
		y_plot_max = -int(yplot * ymax/xmin)
		x_plot_min = -xplot
		y_plot_min = -int(yplot * ymin/xmin)
	elif range_x == 1 and range_y == 2 and abs(xmin) < abs(ymax-ymin):	# x values negateive, y values mixed, y is greater
		x_plot_max = 0
		y_plot_max = int(yplot * (ymax/(ymax-ymin)))
		x_plot_min = int(xplot * xmin/abs(ymax-ymin))
		y_plot_min = int(xplot * (ymin/(ymax-ymin)))
	elif range_x == 2 and range_y == 2 and (xmax-xmin) > (ymax-ymin):	# x values mixed, y values mixed, x is greater
		x_plot_max = int(xplot * xmax/(xmax-xmin))
		y_plot_max = int(yplot * ymax/(xmax-xmin))
		x_plot_min = int(xplot * xmin/(xmax-xmin))
		y_plot_min = int(yplot * ymin/(xmax-xmin))
	else:																# x values mixed, y values mixed, y is greater
		x_plot_max = int(xplot * xmax/(ymax-ymin))
		y_plot_max = int(yplot * ymax/(ymax-ymin))
		x_plot_min = int(xplot * xmin/(ymax-ymin))
		y_plot_min = int(yplot * ymin/(ymax-ymin))
		
	# For troubleshooting, the next line displays the values of the plot size variables.
	# print '\n\nx_plot_max %d  x_plot_min %d  y_plot_max %d  y_plot_min %d' % (x_plot_max,x_plot_min,y_plot_max,y_plot_min)
	
	# The if statement below sclaes the values in the coord_list to fit the defined plot size.
	if range_x != 2 and range_y !=2: 	# If there is no mixing of pos/neg values in both and and y.
		coord_list_scaled = [[coord_list[i]*((x_plot_max - x_plot_min)/max(abs(xmax),abs(xmin))),coord_list[i+1]*((y_plot_max - y_plot_min)/max(abs(ymax),abs(ymin)))] for i in range(0,len(coord_list),2)]
	elif range_x == 2 and range_y !=2:	# If there are pos/neg vales in x but not y.
		coord_list_scaled = [[coord_list[i]*((x_plot_max - x_plot_min)/abs(xmax-xmin)),coord_list[i+1]*((y_plot_max - y_plot_min)/max(abs(ymax),abs(ymin)))] for i in range(0,len(coord_list),2)]
	elif range_x !=2 and range_y == 2:	# If there are pos/neg values in y but not x.
		coord_list_scaled = [[coord_list[i]*((x_plot_max - x_plot_min)/max(abs(xmax),abs(xmin))),coord_list[i+1]*((y_plot_max - y_plot_min)/(ymax-ymin))] for i in range(0,len(coord_list),2)]
	else:								# If there are pos/neg values in both x and y.
		coord_list_scaled = [[coord_list[i]*((x_plot_max - x_plot_min)/abs(xmax-xmin)),coord_list[i+1]*((y_plot_max - y_plot_min)/(ymax-ymin))] for i in range(0,len(coord_list),2)]
	
	# The next line was the old caclulation that the above if statment replaced. It is simpler but only works when all coordinate values are positive:
	# coord_list_scaled = [[coord_list[i]*(x_plot_max/xmax),coord_list[i+1]*(y_plot_max/ymax)] for i in range(0,len(coord_list),2)]

	# The remaining code in this function prints the a plot based on the coordinates from the input .txt file.
	
	# This loop prints 'y' above the y axis.
	for x in range (x_plot_min,x_plot_max + 1):
		if x == 0: print '\by',
		else: print '\b ',
	print ''
	
	# The following loop prints the plot of coordinates.
	for y in range (y_plot_max,y_plot_min-1,-1):				# Iterates from y_plot_max down to y_plot_min. This loop increments with each new line (carriage return).
		print '\b'
		for x in range (x_plot_min,x_plot_max+1):				# Iterates from x_plot_min to x_plot_max. This loop increments after each character is printed, including spaces.
			pcheck = 0											# pcheck is a plot status check; it is set to 0 at the beginning of the loop 
			for i in range(0,len(coord_list_scaled)):
				if coord_list_scaled[i][1] <= y and coord_list_scaled[i][1] > y-1 and coord_list_scaled[i][0] <= x and coord_list_scaled[i][0] > x-1:	# checks to see if a coordinate is in this spot
					print '\b*',
					pcheck = 2									# pcheck is set to 2 when a coordinate has been found.
					remover = i
					break										# Breaks this loop once a coordinate is found to prevent printing overlapping points in the wrong spots.
			if pcheck == 0 and y == 0 and x == 0:				# Prints '+' at the plot's origin.
				print '\b+',
				if x == x_plot_max: print '\b x',				# Prints 'x' if the last printed character of the x axis is '+' (the origin).
				pcheck = 1										# pcheck is set to 1 when an axis or origin has been found.
			elif pcheck ==0 and y == 0 and x == x_plot_max:		
				print '\b- x',									# Prints 'x' to the right of the x axis.
				pcheck = 1										# pcheck is set to 1 when an axis or origin has been found.
			elif pcheck == 0 and y == 0:						
				print '\b-',									# Prints the x axis.
				pcheck = 1										# pcheck is set to 1 when an axis or origin has been found.
			elif pcheck == 0 and x == 0:						
				print '\b|',									# Prints the y axis.
				pcheck = 1										# pcheck is set to 1 when an axis or origin has been found.
			if pcheck == 0: print '\b ',
			if pcheck == 2: del coord_list_scaled[remover]		# If a coordinate was found at the current spot, it is deleted from coord_list_scaled so that the next loop has one less item to check.
																# This deletion also allows the program to calculate how many coordinates were not plotted due to overlapping or a rounding error.

	if len(coord_list_scaled) > 0: print '\n\nPoints not displayed due to overlapping or a plot rounding error: %d' % len(coord_list_scaled)
	print '\n'

	
def create_file (input_file_name):				# This function runs if the input text file is formatted correctly. This function outputs a G-Code file.
	input_file = open(input_file_name)			# Opens the input .txt file as read-only.
	units = input_file.readline()				# Reads in the units; must be "in" or "mm".
	units = units.strip()						# Removes the "\n" (carriage return) from the inputted string.
	retract = float(input_file.readline())		# Reads retraction distance, or clearance of the bit above the material.
	depth = float(input_file.readline())		# Reads the drilling depth.
	depth_per = float(input_file.readline())	# Reads the drilling depth per plunge; this value is ignored if it is greater than or equal to the drilling depth.
	f_rate = float(input_file.readline())		# Reads the plunge feed rate.

	output_file_name = input_file_name.replace('.txt','.g')			# Generates the output file name (example.g) from the input file name (example.txt).
	output_file = open(output_file_name, 'w+')						# The 'w+' opens the file to write and creates the file if none exists. NOTE: There is no confirmation when overwriting an existing file.

	if units == 'in':												# Writes the 1st line of G-Code: sets the units.
		output_file.write('G20 (inches)\n')
	else:
		output_file.write('G21 (millimeters)\n')

	output_file.write('G0Z%.3f (go to retract height)\n' % retract)	# Writes the 2nd line of G-Code: Retracts the router bit to the retract height.
	output_file.write('G0X0.000Y0.000Z%.3f\n' % retract)			# Writes the 3rd line of G-Code: Sends the router bit to the coordinate: (0,0,retract height).
	
	coord_list = []						# Coordinate list. Used only for printing the coordinates to the screen and for the plot; not used for writing coordinates to the G-Code file.
	while True:							# This loop writes the G-Code for each coordinate until the end of the input file is reached.
		blank = input_file.readline()
		if len(blank) == 0: break		# Exits the loop at the end of file.
		x = input_file.readline()		# Reads in x as a string.
		x = x.strip()					# Removes the "\n" (carriage return) from the inputted string.
		if len(x) == 0: break			# Exits the loop if user's text file has extra carriage returns after the final coordinate (protection from poor formatting).
		y = input_file.readline()		# Reads in y as a string.
		y = y.strip()					# Removes the "\n" (carriage return) from the inputted string.
		if len(y) == 0: break			# Exits the loop if user's text file has extra carriage returns after the final coordinate (protection from poor formatting).
		x = float(x)					# Converts x from a string to a float.
		y = float(y)					# Converts y from a string to a float.
		
		coord_list.append(x)			# Adds the current x coordinate to the list
		coord_list.append(y)			# Adds the current y coordinate to the list
		
		if len(coord_list) == 2:
			xmin = x
			xmax = x
			ymin = y
			ymax = y
		else:
			if x < xmin: xmin = x
			if x > xmax: xmax = x
			if y < ymin: ymin = y
			if y > ymax: ymax = y
		
	# This code segment looks at the router distance traveled using the coordinates in their original input order.	
	total_dist = ((coord_list[0])**2 + (coord_list[1])**2)**.5
	for i in range (0,len(coord_list)-2,2):
		current_dist = ((coord_list[i+2]-coord_list[i])**2 + (coord_list[i+3]-coord_list[i+1])**2)**.5
		total_dist += current_dist
	total_dist += (coord_list[len(coord_list)-2]**2 + coord_list[len(coord_list)-1]**2)**.5
	
	# This code segment uses a breadth first search to attempt to shorten the total distance traveled by the router.
	coord_list_check = [coord_list[i] for i in range(0,len(coord_list))]			# Copies the values in coord_list into coord_list_check.
	coord_list_bfs = []																# Initializes the breadth first search coord list.
	check = [0,0]																	# The first check starts at the origin.
	total_dist_bfs = 0 																# Initializes the breadth first search (BFS) travel distance.
	for k in range(0, len(coord_list),2):
		min_dist = ((coord_list_check[0])**2 + (coord_list_check[1])**2)**.5		# Sets a starting value for checking distances, in this case, the distacnce from the origin to the first point in the list.
		min_dist_num = 1															# Sets a starting value for the list index assocaiated with the minimum distance, in this case, 1.
		for i in range(0, len(coord_list_check), 2):
			current_dist = ((coord_list_check[i]-check[0])**2 + (coord_list_check[i+1]-check[1])**2)**.5		# Looks at the distance between check and the coord_list_check.
			if current_dist <= min_dist:											# Sets the min value and min value num if the current checked value is lower than the previous min value.
				min_dist = current_dist
				min_dist_num = i
			if len(coord_list_check) == 2: min_dist_num = 0
		check = [coord_list_check[min_dist_num],coord_list_check[min_dist_num+1]]	# Check is assigned to the coordinates that were just found to be the min distance.
		coord_list_bfs.append(coord_list_check[min_dist_num])		# Adds the next "optimal" x value to the bfs coord list.
		coord_list_bfs.append(coord_list_check[min_dist_num+1])		# Adds the next "optimal" y value to the bfs coord list.
		del coord_list_check[min_dist_num]							# Deletes the x coord value from the check coord list that was just used in the bfs coord list.
		del coord_list_check[min_dist_num]							# Deletes the y coord value from the check coord list that was just used in the bfs coord list.
		total_dist_bfs += min_dist
	total_dist_bfs += (check[0]**2 + check[1]**2)**.5

	# This if statement looks at the original travel distance and the BFS (breadth first search) travel distance and tells the final coord list use which ever one is less.
	if total_dist_bfs < total_dist: coord_list_final = [coord_list_bfs[i] for i in range(0,len(coord_list))]
	else: coord_list_final = [coord_list[i] for i in range(0,len(coord_list))]

	# This code segment writes the g code for travel and plunging, then closes the input and output files.
	for i in range (0,len(coord_list_final),2):
		output_file.write('G0X%.3fY%.3fZ%.3f (go to hole coordinate %d)\n' % (coord_list_final[i], coord_list_final[i+1], retract, (i+2)/2))	# Writes the G-Code to move the router bit to the current coordinate.
		if depth_per >= depth:			
			plunge_once(depth, f_rate, i, output_file)						# This runs if only one plunge is needed per coordinate; spindle plunges once and then moves to the next hole coordinate.
		else:
			plunge_mult(depth, depth_per, f_rate, i, output_file)			# This runs if multiple plunges per hole coordinate are required.
		output_file.write('G0Z%.3f (retract)\n' % retract)					# Writes a retract command to the G-Code file.
	output_file.write('M30 (end of program)')								# Writes an end of program command to the G-Code file.
	input_file.close()														# Closes the input .txt file.
	output_file.close()	
	
	# Clears the screen.
	if _platform == "linux" or _platform == "linux2":						
		os.system('clear')  # Linux
	elif _platform == "darwin":
	   os.system('clear')   # Mac OS X
	elif _platform == "win32":
		os.system('cls')    # Windows
	
	# Once the G-Code file has been created, information is displayed about that file.
	print '\nG-Code file "%s" has been generated.\n' % output_file_name
	print '%d holes will be drilled with the following parameters:\n' % ((i+2)/2)
	print 'Retract Height:   %s %s' % (retract, units)
	print 'Drill Depth:      %s %s' % (depth, units)
	if depth_per < depth: print 'Depth Per Pass:   %s %s' % (depth_per, units)
	print 'Plunge Feed Rate: %s %s/min\n' % (f_rate, units)

	# The min and max values are printed as a double check for the user. If any values that were typed in are way off, it should be apparent here.
	print 'x Min = %.3f     x Max = %.3f     y Min = %.3f     y Max = %.3f' % (xmin, xmax, ymin, ymax)	
	
	# if the BFS decreased overall travel, this will print by how much.
	if total_dist_bfs < total_dist: print '\nBy changing hole order, travel time was decreased by %.0f%% (%.1f %s):\n' % (100-(total_dist_bfs/total_dist)*100, total_dist-total_dist_bfs, units)	
	else: print '\nCoordinates to drill:\n'
	# All the coordinates are printed, 4 per row, as another double check for the user.
	linecheck = 0
	for i in range(0,len(coord_list_final),2):									# Increments by 2 each time
		print '(%.3f, %.3f) ' % (coord_list_final[i],coord_list_final[i+1]),	# prints the coordinates to 3 decimal places
		linecheck += 1
		if linecheck % 4 == 0: print '\n'							# Starts a new line after 4 coordinates are pritned.
	plot(xmin,xmax,ymin,ymax,coord_list)							# Runs the 'plot' function to draw the graph of coordinates.
	
	
	
	
# Clears the screen.
import os																
from sys import platform as _platform
if _platform == "linux" or _platform == "linux2":
	os.system('clear')  # Linux
elif _platform == "darwin":
   os.system('clear')   # Mac OS X
elif _platform == "win32":
	os.system('cls')    # Windows	

intro()											# Runs the Intro function.
print '\nEnter text file name: ',
input_file_name = raw_input()					# User types the input .txt file name. 
errorcode = format_check(input_file_name)		# Runs the Format Check function and returns an Error Code.
if errorcode == 0:								# Runs the 'create_file' function if no formatting errors were found in the input .txt file (errorcode = 0).
	create_file(input_file_name)
else:											# If a formatting error was found in the input .txt file, one of the following error messages will display.
	if   errorcode == 1: print 'There is a problem with the units.',
	elif errorcode == 2: print 'There is a problem with the drilling/plunge parameters.',
	elif errorcode == 3: print 'A blank line is missing between the parameters and the coordinates.',
	else:           	 print 'There is a problem with the coordinates.',
	print ' Please check the formatting of %s.' % input_file_name