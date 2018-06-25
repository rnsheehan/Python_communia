import os
import glob
# access system routines

import Common
import Plotting

# The aim of this module is to be able to read .s2p files as they are output by the VNA
# You should be able to make a plot of the S_{ij} data from a given file
# You should be able to make an estimate of the 3dB FR from a data set 
# R. Sheehan 26 - 9 - 2017

def read_s2p_file(s2pfile, delimiter = " ", loud = False):
    # method for reading the data in an s2p file
    # for more info see 
    # http://na.support.keysight.com/plts/help/WebHelp/FilePrint/SnP_File_Format.htm 
    # http://na.support.keysight.com/pna/help/WebHelp7_5/S1_Settings/Data_Format_and_Scale

    # Lines that contain symbol ! are comment lines
    # Lines that contain symbol # are option lines

    # function returns a list of the form 
    # list[0] = options
    # list[1] = frequency
    # list[2] = S_{11}
    # list[3] = S_{21}
    # list[4] = S_{12}
    # list[5] = S_{22}

    # R. Sheehan 2 - 4 - 2017

    try:
        if glob.glob(s2pfile):

            thefile = file(s2pfile,"r") # open file for reading

            # file is available for reading
            thedata = thefile.readlines() # read the data from the file

            nrows = Common.count_lines(thedata, s2pfile) # count the number of rows

            if loud: 
                print "%(path)s is open"%{"path":s2pfile}
                print "Nrows = ",nrows

            # s2p file consists of header data followed by complex S_{ij} frequency response data in the form
            # frequency S_{11}^{real} S_{11}^{imag} S_{21}^{real} S_{21}^{imag} S_{12}^{real} S_{12}^{imag} S_{22}^{real} S_{22}^{imag}

            # or it could be exported in dB scale with phase data
            # 0         1                    2              3                    4              5                    6              7                    8
            # frequency log mag. S_{11} (dB) S_{11}^{phase} log mag. S_{21} (dB) S_{21}^{phase} log mag. S_{12} (dB) S_{12}^{phase} log mag. S_{22} (dB) S_{22}^{phase}

            # lists to store the retrieved data
            # to be honest I'm only interested in the log mag data
            Frequency = []; options = ""
            S11 = []; S21 = [];
            S12 = []; S22 = [];

            #f_3dB = 0.0; S12_3dB = 0.0;

            #cnt = 0; fcnt = 0;
            #Rmax = -200.0; tmp = 0.0; indx = 0
            for line in thedata:
                parameters = line.split(delimiter)

                if "#" in line: options = line

                if Common.isfloat(parameters[0]):
                    # store the data
                    Frequency.append( float( parameters[0] )/1.0e+9 ) # store frequency in units og GHz
                    S11.append( float( parameters[1] ) )
                    S21.append( float( parameters[3] ) )
                    S12.append( float( parameters[5] ) )
                    S22.append( float( parameters[7] ) )

                    # find the max S_{11} value, max RF reflection from DUT
                    #tmp = float( parameters[1] )
                    #if tmp > Rmax: Rmax = tmp; indx_Rmax = indx

                    # set the 3_dB limit value
                    #if fcnt == 0: 
                    #    S12_3dB = float( parameters[3] ) - 3.0
                    #    fcnt = 1

                    # check if the 3dB limit is reached
                    #if fcnt == 1 and abs(float( parameters[3] ) - S12_3dB) < 1.0e-6:
                    #    f_3dB = float( parameters[0] )/1.0e+9
                    #    print "f3dB =",f_3dB,"(GHz)"
                    #    fcnt = 2

                    # check if the 3dB limit is reached
                    #if fcnt == 1 and float( parameters[3] ) < S12_3dB:
                    #    f_3dB = float( parameters[0] )/1.0e+9
                    #    if loud: print "f3dB =",f_3dB,"(GHz)"
                    #    fcnt = 2

                    #indx += 1
                    
            # f_3dB > 50 (GHz), will you ever see the day?
            #if fcnt == 1: f_3dB = 50.0
            
            #s2p_dict = {'Options':options, 'f_3dB':f_3dB, 'S_3dB':S12_3dB, 'f_Rmax':Frequency[indx_Rmax], 'Rmax':Rmax}
            s2p_dict = {'Options':options,'Title':s2pfile.replace(".s2p","")}

            return [s2p_dict, Frequency, S11, S21, S12, S22]
        else:
            print "Error: Cannot find ",filename
            raise Exception
    except Exception:
        print "Error: TIPS_FR_Analysis.read_s2p_file"
        return None

def estimate_f3dB(s2pdata, loud = False):
    # estimate 3dB BW from a measured S_{21} data set

    try:
        if s2pdata is not None:
            
            fr_indx = 1
            s_param = 3 # index of S_{21} data as it is stored in s2pdata object
            start_fr = 1.0 # estimate f_{3dB} starting from frequency of 1 GHz
            max_fr = max(s2pdata[fr_indx]) # max frequency stored in data set

            if loud: print "start_fr =",start_fr,", max_fr =",max_fr

            if start_fr < max_fr:
                # what is the response value at f = 1 GHz?
                start_loc = 0; tol = 1.0E-3; loud_here = False; rec_dep = 0; 
                resp_fr_indx, start_fr = Common.list_search(s2pdata[fr_indx], start_fr, start_loc, tol, loud_here, rec_dep)
                resp_init = s2pdata[s_param][resp_fr_indx] # store S_{21} value where freq. = start_fr
                resp_3dB = resp_init - 3.0 # S_{21} value after it's dropped by 3dB

                # what is the frequency where response has dropped by 3dB?
                tol = 1.0E-3; loud_here = False; rec_dep = 0; 
                resp_bw_indx, resp_bw_val = Common.list_search(s2pdata[s_param], resp_3dB, resp_fr_indx, tol, loud_here, rec_dep)
                resp_bw_fr = s2pdata[fr_indx][resp_bw_indx]                

                if loud:
                    print "S_{21}(%(v1)0.2f) = %(v2)0.2f"%{"v1":start_fr,"v2":resp_init}
                    print "S_{21}(%(v1)0.2f) = %(v2)0.2f\n"%{"v1":resp_bw_fr,"v2":resp_bw_val}

                return resp_bw_fr # return the estimate 3dB BW value
            else:
                print "start_fr =",start_fr," > max_fr =",max_fr
                return 1.0
                raise Exception
        else:
            print "No data stored in s2pdata"
            raise Exception
    except Exception:
        print "\nError: FR_Analysis.estimate_f3dB"

def estimate_Rmax(s2pdata, loud = False):
    # estimate the max "loss" from S_{11}, S_{22} data set

    pass

def plot_s2p_data(s2pdata, s_param = 3, loud = False):
    # plot some measured S_{ij} that has been read from an s2p file
    # assumes DUT is connected to port 1 and Rx is connected to port 2

    # s2p_data comprises a list with elements of the form
    # s2p_data[0] = dictonary that contains information on the data set
    # s2p_data[1] = Frequency (GHz)
    # s2p_data[2] = S_{11} (dB), use this to plot RF reflection from DUT
    # s2p_data[3] = S_{21} (dB), use this to plot FR of DUT
    # s2p_data[4] = S_{12} (dB), use this to plot X-Talk between DUT and Rx
    # s2p_data[5] = S_{22} (dB), use this to plot RF reflection from Rx

    # s_param is an integer equal to 2,3,4,5 that specifies what data should be plotted
    
    # R. Sheehan 3 - 4 - 2017

    try:
        if s2pdata is not None:
            
            # re-set s_param value if it has been entered incorrectly
            # default plot will be the S_{21} data
            if s_param < 2 or s_param > 5: s_param = 3

            args = Plotting.plot_arg_single()

            args.x_label = 'Frequency (GHz)'
            
            # set the y-label accoring to what's being plotted
            if s_param == 2:args.y_label = '$S_{11}$ (dB)'
            elif s_param == 3: args.y_label = '$S_{21}$ (dB)'
            elif s_param == 4: args.y_label = '$S_{12}$ (dB)'
            elif s_param == 5: args.y_label = '$S_{22}$ (dB)'
            else: args.y_label = '$S_{12}$ (dB)'
            
            args.marker = 'r-'
            args.fig_name = s2pdata[0]['Title']
            if s_param == 2:args.fig_name += "_S11"
            elif s_param == 3: args.fig_name += "_S21"
            elif s_param == 4: args.fig_name += "_S12"
            elif s_param == 5: args.fig_name += "_S22"
            else: args.fig_name += "_S21"
            args.loud = loud
            args.plt_range = [1, 15, -30, -12]

            Plotting.plot_single_curve(s2pdata[1], s2pdata[s_param], args)
        else:
            raise Exception
    except Exception:
        print "\nError: FR_Analysis.plot_s2p_data"

def multiple_FR_plot(dir_name, file_names, labels, s_param, plot_range, plt_title = '', plt_name = '', loudness = False):

    # plot the measured S21 data at multiple biases

    try:
        HOME = os.getcwd()

        if os.path.isdir(dir_name):
            os.chdir(dir_name)

            # test inputs for validity
            c1 = True if file_names is not None else False
            c2 = True if labels is not None else False
            c3 = True if len(file_names) == len(labels) else False
            c4 = True if plot_range is not None else False
            c5 = True if len(plot_range) == 4 else False
            c6 = True if c1 and c2 and c3 and c4 and c5 else False

            if c6:
                T = 0.0; VEAM = 0.0; name = ""
                hv_data = []; markers = []; 

                count = 0
                for i in range(0, len(file_names), 1):
                    if glob.glob(file_names[i]):
                        s2pdata = read_s2p_file( file_names[i] ); # read s2p data from file
                        hv_data.append([ s2pdata[1], s2pdata[s_param] ]); # store data needed for plot
                        markers.append( Plotting.labs_lins[i%len(Plotting.labs_lins)] ) # make a list of markers                
                        del s2pdata
                    else:
                        # this will raise an exception below
                        print "\nError: FR_Analysis.multiple_FR_plot()\nCould not locate:",file_names[i]

                # Need to have number of data sets equal to number of labels for plotting methods to work
                if len(hv_data) == len(labels):
                    args = Plotting.plot_arg_multiple()

                    args.loud = loudness
                    args.crv_lab_list = labels
                    args.mrk_list = markers
                    args.x_label = 'Frequency (GHz)'
            
                    # assign y-axis label based on S-parameter being plotted
                    if s_param == 2:args.y_label = '$S_{11}$ (dB)'
                    elif s_param == 3: args.y_label = '$S_{21}$ (dB)'
                    elif s_param == 4: args.y_label = '$S_{12}$ (dB)'
                    elif s_param == 5: args.y_label = '$S_{22}$ (dB)'
                    else: args.y_label = '$S_{12}$ (dB)'

                    args.plt_range = plot_range
                    args.plt_title = plt_title            
                    args.fig_name = plt_name

                    if s_param == 2:args.fig_name += "_S11"
                    elif s_param == 3: args.fig_name += "_S21"
                    elif s_param == 4: args.fig_name += "_S12"
                    elif s_param == 5: args.fig_name += "_S22"
                    else: args.fig_name += "_S21"

                    Plotting.plot_multiple_curves(hv_data, args)

                    del hv_data
                    del markers
                else:
                    raise Exception
                os.chdir(HOME)
            else:
                raise Exception
        else:
            raise EnvironmentError
    except EnvironmentError:
        print "\nError: FR_Analysis.multiple_FR_plot()"
        print "Cannot find",dir_name
    except Exception:
        print "\nError: FR_Analysis.multiple_FR_plot()"
        if c1 == False: print "dir_names not assigned correctly"
        if c2 == False: print "labels not assigned correctly"
        if c3 == False: print "dir_names and labels have different lengths"
        if c4 == False: print "range not assigned correctly"
        if c5 == False: print "range does not have correct length"


