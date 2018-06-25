import os
import glob
import re
import sys # access system routines

import math
import scipy
import numpy as np
import matplotlib.pyplot as plt

import Common
import Plotting

# The aim of this module is to be able to read BER data in the format I currently have it stored
# Then make plots of single / multiple BER curves
# Need to plot data in raw measured format and also in the formatted format, whereby measured BER data is converted into loglog form
# and plotted with special tick markers and labels
# It should also be possible to compute receiver sensitivity at a given BER level
# R. Sheehan 25 - 9 - 2017

def read_BER_data_old(ber_file, loud = False):

    # method for reading the data associated with a BER measurement
    # data in older format files is stored in the form
    # 10% PRx / dBm, BER
    # R. Sheehan 23 -3 - 2017

    try:
        if glob.glob(ber_file):
            
            thefile = file(ber_file,"r") # open file for reading

            # file is available for reading
            thedata = thefile.readlines() # read the data from the file

            nrows = Common.count_lines(thedata, ber_file) # count the number of rows

            if loud: 
                print "%(path)s is open"%{"path":ber_file}
                print "Nrows = ",nrows

            # declare a dictionary to save the paramaters associated with a particular BER test
            ber_dict = {}

            # declare lists to store Rx power data and Measured BER values
            PRx_dBm = [] # stored received power value is 10% of true value
            BER_vals = []
            param_titles = []
            param_values = []

            for line in thedata:
                parameter = line.split(',')
                if Common.isfloat(parameter[0]):
                    # you've reached the data   
                    p_val = float( parameter[0] )                 
                    #PRx_dBm.append( Common.convert_Split_Power_Reading( p_val, sr_low, sr_high)  )
                    #PRx_dBm.append( -1.0*(abs(p_val/2.4575062) )  ) # x_{90} = x_{10} / 2.4575062
                    PRx_dBm.append(9.575235+1.006838*p_val) # x_{90} = 9.575235 + 1.006838 x_{10}, see notebook 2715, page 79

                    BER_vals.append( float(parameter[1].replace("\n","") ) )
                else:
                    param_titles.append( parameter[0] )
                    param_values.append( parameter[1].replace("\n","") )
               
            # use the in-built zip function to create the dictionary
            ber_dict = dict( zip(param_titles, param_values) )

            ber_dict.update({'Title':ber_file.replace(".csv","")})

            del ber_dict['Experiment Parameters']
            del ber_dict['Pout (dBm) @ 10%']
            del param_titles
            del param_values

            if not PRx_dBm and not BER_vals:
                raise Exception
            else:
                print "Data acquired from",ber_file
                return [True, ber_dict, PRx_dBm, BER_vals]
        else:
            # file cannot be found
            raise Exception
    except Exception:
        print "Error: BER_Analysis.Read_BER_Data"
        if thefile.closed:"Error: Cannot Open File",ber_file
        return None

def read_BER_data(ber_file, loud = False):

    # method for reading the data associated with a BER measurement
    # R. Sheehan 23 -3 - 2017
    # Updated R. Sheehan 25 - 9 - 2017
    # data in newer format files is stored in the form
    # 10% PRx / dBm, 90% PRx / dBm, BER

    # In the most recent measurements the 90-10 splitter was replaced with a 98-2 splitter to reduce insertion loss
    # Certain lines have been changed to reflect this
    # R. Sheehan 13 - 2 - 2018

    # object returned is a list of the form
    # list[0] = True indicates that data has been read successfully
    # list[1] = ber_dict is a dictionary containing the pre-amble text for the data file, in this case a list of the experiment parameters
    # list[2] = PRx_dBm measured received power from the 90% arm of the splitter, see notebook 2715 page 159 for experimental setup
    # list[3] = BER_vals list of unformatted BER values, i.e. readings taken directly from EA unit
    # list[4] = formatted BER-vals

    try:
        if glob.glob(ber_file):
            
            thefile = file(ber_file,"r") # open file for reading

            # file is available for reading
            thedata = thefile.readlines() # read the data from the file

            nrows = Common.count_lines(thedata, ber_file) # count the number of rows

            if loud: 
                print "%(path)s is open"%{"path":ber_file}
                print "Nrows = ",nrows

            # declare a dictionary to save the paramaters associated with a particular BER test
            ber_dict = {}

            # declare lists to store Rx power data and Measured BER values
            PRx_dBm = [] # stored received power value is 90% of true value
            BER_vals = [] # stored measured BER values
            formatted_BER_vals = [] # format measured BER values for log(BER) plot
            param_titles = []
            param_values = []

            # output the tck markers for the formatted BER plot
            #y_tck_vals = [-3.0103,   -4.7712,   -6.0206,   -6.9897,   -7.7815, -8.4510,    -9.0309,   -9.5424,     -10,    -10.4139,  -10.7918]
            #y_tck_labs = [r'1.0E-2', r'1.0E-3', r'1.0E-4', r'1.0E-5', r'1.0E-6', r'1.0E-7', r'1.0E-8', r'1.0E-9', r'1.0E-10', r'1.0E-11', r'1.0E-12']
            
            #y_tck_vals = [-3.0103,   -4.7712,   -6.0206,   -6.9897,   -7.7815,  -8.4510,    -9.0309,  -9.5424]
            #y_tck_labs = [r'1.0E-2', r'1.0E-3', r'1.0E-4', r'1.0E-5', r'1.0E-6', r'1.0E-7', r'1.0E-8', r'1.0E-9']

            y_tck_vals = [-3.0103,   -4.7712,   -6.0206,   -6.9897,   -7.7815]
            y_tck_labs = [r'1.0E-2', r'1.0E-3', r'1.0E-4', r'1.0E-5', r'1.0E-6']

            for line in thedata:
                parameter = line.split(',')
                if Common.isfloat(parameter[0]):
                    # you've reached the data                       
                    PRx_dBm.append( float( parameter[1] ) ) # conversion from 2% to 98% data is done inside the file

                    value = float( parameter[2].replace("\n","") ) # measured BER from file

                    BER_vals.append( value )
                    # format BER value for plotting
                    # -10.0*math.log10( -1.0*math.log10(item[3][i]) )
                    formatted_BER_vals.append( -10.0*math.log10(-1.0*math.log10( value )) )
                else:
                    param_titles.append( parameter[0] )
                    param_values.append( parameter[1].replace("\n","") )
               
            # use the in-built zip function to create the dictionary
            ber_dict = dict( zip(param_titles, param_values) )

            ber_dict.update({'Title':ber_file.replace(".csv","")})
            ber_dict.update({'y_labs':y_tck_labs})
            ber_dict.update({'y_vals':y_tck_vals})

            del ber_dict['Experiment Parameters']
            #del ber_dict['Pout (dBm) @ 2%']
            del param_titles
            del param_values

            if not PRx_dBm and not BER_vals:
                raise Exception
            else:
                print "Data acquired from",ber_file
                return [True, ber_dict, PRx_dBm, BER_vals, formatted_BER_vals]
        else:
            # file cannot be found
            raise Exception
    except Exception:
        print "Error: BER_Analysis.Read_BER_Data"
        if thefile.closed:"Error: Cannot Open File",ber_file
        return None

def plot_raw_BER_data(ber_data, loud = False):

    # make a plot of the unformatted BER data
    
    # R. Sheehan 25 - 9 - 2017

    # read_BER_data returns a list of the form
    # list[0] = True indicates that data has been read successfully
    # list[1] = ber_dict is a dictionary containing the pre-amble text for the data file, in this case a list of the experiment parameters
    # list[2] = PRx_dBm measured received power from the 90% arm of the splitter, see notebook 2715 page 159 for experimental setup
    # list[3] = BER_vals list of unformatted BER values, i.e. readings taken directly from EA unit
    # list[4] = formatted BER-vals

    try:
        if ber_data[0] is True:
            args = Plotting.plot_arg_single()

            args.x_label = '$P_{Rx}$ (dBm)'
            args.y_label = 'BER'
            args.plt_range = [min(ber_data[2]), max(ber_data[2]), min(ber_data[3]), max(ber_data[3])]
            args.loud = loud
            args.log_y = True # set y-axis scale to be a log scale
            args.fig_name = ber_data[1]['Title']
            args.plt_title = 'BER direct from Error Analyser'
            args.marker = 'b*'

            Plotting.plot_single_curve(ber_data[2], ber_data[3], args)
        else:
            raise Exception
    except Exception:
        print "\nError: BER_Analysis.plot_raw_BER_data\n"
        if ber_data[0] is False: print "BER data not read correctly\n"

def plot_multiple_raw_BER_data(ber_data_list, label_list, figure_name, plot_title, loud = False):

    # plot multiple BER data sets on the same figure
    # R. Sheehan 11 - 10 - 2017

    # read_BER_data returns a list of the form
    # list[0] = True indicates that data has been read successfully
    # list[1] = ber_dict is a dictionary containing the pre-amble text for the data file, in this case a list of the experiment parameters
    # list[2] = PRx_dBm measured received power from the 90% arm of the splitter, see notebook 2715 page 159 for experimental setup
    # list[3] = BER_vals list of unformatted BER values, i.e. readings taken directly from EA unit
    # list[4] = formatted BER-vals

    try:
        if ber_data_list is not None:
            
            hv_data = []; markers = [];

            count = 0
            for i in range(0, len(ber_data_list), 1):
                hv_data.append( [ ber_data_list[i][2], ber_data_list[i][3] ] )
                markers.append(Plotting.labs_pts[count])
                count = (count+1)%len(Plotting.labs_pts)
            
            args = Plotting.plot_arg_multiple()

            args.x_label = '$P_{Rx}$ (dBm)'
            args.y_label = 'BER'
            #args.plt_range = [min(ber_data[2]), max(ber_data[2]), min(ber_data[3]), max(ber_data[3])]
            args.loud = loud
            args.log_y = True # set y-axis scale to be a log scale
            args.fig_name = figure_name
            args.plt_title = plot_title
            args.crv_lab_list = label_list
            args.mrk_list = markers

            Plotting.plot_multiple_curves(hv_data, args)

            del hv_data; del markers; 

        else:
            raise Exception
    except Exception:
        print "Error: BER_Analysis.plot_multiple_raw_BER_data"
        if ber_data_list is None: print "BER data not read correctly\n"

def plot_formatted_BER_data(ber_data, loud = False):

    # make a plot of the formatted BER data
    
    # R. Sheehan 26 - 9 - 2017

    # read_BER_data returns a list of the form
    # list[0] = True indicates that data has been read successfully
    # list[1] = ber_dict is a dictionary containing the pre-amble text for the data file, in this case a list of the experiment parameters
    # list[2] = PRx_dBm measured received power from the 90% arm of the splitter, see notebook 2715 page 159 for experimental setup
    # list[3] = BER_vals list of unformatted BER values, i.e. readings taken directly from EA unit
    # list[4] = formatted BER-vals

    try:
        if ber_data[0] is True:
            args = Plotting.plot_arg_single()

            args.x_label = '$P_{Rx}$ (dBm)'
            args.y_label = '-log(BER)'
            args.plt_range = [min(ber_data[2]), max(ber_data[2]), min(ber_data[4]), max(ber_data[4])]
            args.loud = loud
            args.fig_name = 'Fmttd_' + ber_data[1]['Title']
            args.plt_title = 'BER versus Received Power'
            args.y_tck_vals = ber_data[1]['y_vals']
            args.y_tck_labs = ber_data[1]['y_labs']

            Plotting.plot_single_linear_fit_curve(ber_data[2], ber_data[4], args)
        else:
            raise Exception
    except Exception:
        print "\nError: BER_Analysis.plot_formatted_BER_data\n"
        if ber_data[0] is False: print "BER data not read correctly\n"

def plot_multiple_formatted_BER_data(ber_data_list, label_list, figure_name, plot_title, loud = False):

    # plot multiple BER data sets on the same figure
    # R. Sheehan 11 - 10 - 2017

    # read_BER_data returns a list of the form
    # list[0] = True indicates that data has been read successfully
    # list[1] = ber_dict is a dictionary containing the pre-amble text for the data file, in this case a list of the experiment parameters
    # list[2] = PRx_dBm measured received power from the 90% arm of the splitter, see notebook 2715 page 159 for experimental setup
    # list[3] = BER_vals list of unformatted BER values, i.e. readings taken directly from EA unit
    # list[4] = formatted BER-vals

    try:
        if ber_data_list is not None:
            hv_data = []; markers = [];

            count = 0
            for i in range(0, len(ber_data_list), 1):
                hv_data.append( [ ber_data_list[i][2], ber_data_list[i][4] ] )
                markers.append(Plotting.labs_pts[count])
                count = (count+1)%len(Plotting.labs_pts)
            
            args = Plotting.plot_arg_multiple()

            args.x_label = '$P_{Rx}$ (dBm)'
            args.y_label = '-log(BER)'
            args.plt_range = [-16, -10, -8, -3]
            #args.plt_range = [-17, -11, -9, -3]
            args.loud = loud
            args.fig_name = figure_name
            args.plt_title = plot_title
            args.crv_lab_list = label_list
            args.mrk_list = markers
            args.y_tck_vals = ber_data_list[0][1]['y_vals']
            args.y_tck_labs = ber_data_list[0][1]['y_labs']

            Plotting.plot_multiple_linear_fit_curves(hv_data, args)

        else:
            raise Exception
    except Exception:
        print "Error: BER_Analysis.plot_multiple_formatted_BER_data"
        if ber_data_list is None: print "BER data not read correctly\n"

def compute_Rx_sensitivity(ber_data, ber_level, loud = False):

    # compute the Rx sensitivity based on a measured BER data set
    # perform a linear fit to the formatted data
    # use the linear fit to estimate the received power closest to a given BER level
    # R. Sheehan 26 - 9 - 2017

    # read_BER_data returns a list of the form
    # list[0] = True indicates that data has been read successfully
    # list[1] = ber_dict is a dictionary containing the pre-amble text for the data file, in this case a list of the experiment parameters
    # list[2] = PRx_dBm measured received power from the 90% arm of the splitter, see notebook 2715 page 159 for experimental setup
    # list[3] = BER_vals list of unformatted BER values, i.e. readings taken directly from EA unit
    # list[4] = formatted BER-vals

    try:
        if ber_data[0] is True:
            
            # make a linear fit to the formatted measured BER data
            # make the linear fit
            # pars[0] = intercept
            # pars[1] = slope
            pars = Common.linear_fit(np.asarray(ber_data[2]), np.asarray(ber_data[4]), [0, 1])

            if pars is not None:
                # convert the desired BER level to formatted BER level
                fmttd_ber_lvl = -10.0*math.log10(-1.0*math.log10( ber_level ))

                if math.fabs(pars[1]) > 0.0:
                    # estimate the received power at which the the BER level could be achieved
                    # this power level could be outside the range of measured data
                    prx = (fmttd_ber_lvl - pars[0]) / pars[1]

                    if loud:
                        print "Data set:",ber_data[1]['Title']
                        print "fit intercept =",pars[0]
                        print "fit slope =",pars[1]
                        print "BER level:",ber_level
                        print "Formatted BER level:",fmttd_ber_lvl
                        print "Receiver sensitivity (dBm):",prx

                    # write the computed data to a file
                    thepath = ber_data[1]['Title'] + "_Rx_Sens.txt"

                    thefile = file(thepath,"w") # create a file for writing

                    if thefile.closed:
                        print "Could not open file",thepath
                        raise Exception
                    else:
                        thefile.write("Data set: %(v1)s\n\nFit parameters for formatted data\n"%{"v1":ber_data[1]['Title']})
                        thefile.write("intercept: %(v1)0.3f\n"%{"v1":pars[0]})
                        thefile.write("slope: %(v1)0.3f\n\n"%{"v1":pars[1]})
                        thefile.write("BER level: %(v1)0.3E\n"%{"v1":ber_level})
                        #thefile.write("Formatted BER level: %(v1)0.3f\n"%{"v1":fmttd_ber_lvl})
                        thefile.write("Receiver sensitivity (dBm): %(v1)0.3f\n"%{"v1":prx})

                        thefile.close()

                    del thepath
                    del thefile
                    del pars
                else:
                    print "Cannot compute receiver sensitivity for data:",ber_data[1]['Title']
                    print "Linear fit has failed with fit slope =",pars[1]
                    raise Exception
            else:
                print "Linear fit process has failed for data:",ber_data[1]['Title']
                raise Exception
        else:
            raise Exception
    except Exception:
        print "\nError: BER_Analysis.compute_Rx_sensitivity"
        if ber_data[0] is False: print "BER data not read correctly\n"
