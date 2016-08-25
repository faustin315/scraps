import matplotlib.pyplot as plt
import matplotlib.gridspec as gs
import matplotlib as mpl
import numpy as np
import scipy.signal as sps
from .containers import indexResList

def plotResListData(resList, plot_types=['IQ'], **kwargs):
    r"""Plot resonator data and fits.

    Parameters
    ----------
    resList : list-like
        A list of ``pyres.Resonator`` objects. A single ``Resonator`` object can
        be passed, as long as it is in a list.

    plot_types : list, optional
        A list of plots to create, each one specified by a string. Possible plot
        types are:

        - 'IQ': Plots the real part of the transmission (`I`) vs the imaginary
        part (`Q`). This is the default plot.
        - 'rIQ': Plots the residual of `I` vs the residual of `Q`. This plot is
        only available if the ``do_lmfit`` method of each ``Resonator`` object
        has been called. The `I` and `Q` residuals are normalized by the
        uncertainty of the `I` and `Q` data respectively. If this is not
        explicitly supplied, it is calculated by taking the standard deviation
        of the first 10 data points.
        - 'LinMag': Plots the magnitude of the tranmission in Volts vs
        frequency.
        - 'LogMag': Plots the magnitude of the transmission in dB vs frequency.
        ``LogMag = 20*np.log(LinMag)``.
        - 'rMag': Plots the difference of `LinMag` and the best-fit magnitude vs
        frequency. This plot is only available if the ``do_lmfit`` method of
        each ``Resonator`` object has been called.
        - 'Phase': Plots the phase of the transmision vs frequency.
        ``Phase = np.arctan2(Q, I)``.
        - 'rPhase': Plots the difference of `Phase` and the best-fit phase vs
        frequency. This plot is only available if the ``do_lmfit`` method of
        each ``Resonator`` object has been called.
        - 'uPhase': Plots the unwrapped phase vs frequency.
        ``uPhase = np.unwrap(Phase)``.
        - 'ruPhase': Plots the difference of `uPhase` and the unwrapped best-fit
        phase vs frequency. This plot is only available if the ``do_lmfit``
        method of each ``Resonator`` object has been called.
        - 'I': Plots the real part of the transmission vs frequency.
        - 'rI': Plots the residual of `I` vs frequency. The residual is weighted
        by the uncertainty in `I`. This plot is only available if the
        ``do_lmfit`` method of each ``Resonator`` object has been called.
        - 'Q': Plots the imaginary part of the transmission vs frequency.
        - 'rQ': Plots the residual of `Q` vs frequency. The residual is weighted
        by the uncertainty in `Q`. This plot is only available if the
        ``do_lmfit`` method of each ``Resonator`` object has been called.

    plot_fits : {False, True}, optional
        Whether or not to overplot the best fit on the data. This is only
        effective if the  ``do_lmfit`` method of each ``Resonator`` object has
        been called. Default is False.

    powers : list-like, optional
        A list of power values to plot. Default is to plot all of the unique
        powers that exist in the list of ``Resonator`` objects.

    temps : list-like, optional
        A list of temperature values to plot. Default os to plot all of the
        unique temperatures that exist in the list of ``Resonator`` obejcts.

    use_itemps : {False, True}, optional
        If a ``ResonatorSweep`` object has been generated from the resList it
        may have added the ``itemp`` attrubute to each ``ResonatorObject`` in
        the list. Specifying ``use_itemps = True`` will force the plotting
        routine to use those tempeartures.

    freq_units : {'GHz', 'Hz', 'kHz', 'MHz', 'THz'}, optional
        The units for the frequency axis, if it exists. Defaul is 'GHz'.

    detrend_phase : {False, True}, optional
        Whether or not to remove a linear trend from the `Phase` data. A typical
        reason for a steep linear offset in the phase is an uncorrected
        electrical delay due to long transmission lines.

    num_cols : int, optional
        The number of columns to include in the grid of subplots. Default is 1.

    fig_size : int, optional
        The size of an individual subplot in inches. Default is 3.

    force_square : {False, True}, optional
        Whether or not to force each subplot axis to be perfectly square.

    show_colorbar : {True, False}, optional
        Whether or not to add a colorbar to the right edge of the figure. The
        colorbar will correspond to the limits of the colored data. Default is
        True.

    color_by : {'temps', 'pwrs'}, optional
        If multiple temperatures and multiple powers are passed, this selects
        which variable will set the color of the plots. Default is 'temps'.

    color_map : str, optional
        The name of any colormap returned by calling
        ``matplotlib.pyplot.colormaps()`` is a valid option. Default is
        'coolwarm'.

    Returns
    -------
    figS : matplotlib.pyplot.figure

    """
    #TODO: Add temperature and power masking that makes more sense, like the ability
    #to set a temperature range, or maybe decimate the temperature data. Also
    #need to add the ability to waterfall the mag and phase plots.
    supported_types = ['IQ', 'rIQ', 'LogMag', 'LinMag', 'rMag',
                        'Phase', 'rPhase', 'uPhase', 'ruPhase',
                        'I', 'rI', 'Q', 'rQ']
    assert all(plt_key in supported_types for plt_key in plot_types), "Unsupported plotType requested!"

    #Get a list of unique temps and powers
    powers = []
    temps = []

    #Should we use itemps?
    use_itemps = kwargs.pop('use_itemps', False)
    assert all(hasattr(res, 'itemps') for res in resList), "Could not locate itemp for at least one resonator!"

    for res in resList:
        powers.append(res.pwr)
        if use_itemps:
            temps.append(res.itemp)
        else:
            temps.append(res.temp)

    powers = np.unique(powers)
    temps = np.unique(temps)

    #Optionally override either list
    powers = kwargs.pop('powers', powers)
    temps = kwargs.pop('temps', temps)

    #Should we plot best fits?
    plot_fits = kwargs.pop('plot_fits', False)
    assert all(res.hasFit for res in resList), "At least one resonator has not been fit yet."

    #Set the units for the frequency axes
    freq_units = kwargs.pop('freq_units', 'GHz')
    assert freq_units in ['Hz', 'kHz', 'MHz', 'GHz', 'THz'], "Unsupported units request!"

    unitsDict = {'Hz':1,
                'kHz':1e3,
                'MHz':1e6,
                'GHz':1e9,
                'THz':1e12}

    #Remove linear phase variation? Buggy...
    detrend_phase = kwargs.pop('detrend_phase', False)

    #Set some plotting defaults
    num_cols = kwargs.pop('num_cols', 1)
    fig_size = kwargs.pop('fig_size', 3)
    force_square = kwargs.pop('force_square', False)
    show_colorbar = kwargs.pop('show_colorbar', True)

    #Should the temperatures or the powers iterate the colors?
    color_by = kwargs.pop('color_by', 'temps')
    assert color_by in ['temps', 'pwrs'], "color_by must be 'temps' or 'pwrs'."

    #Set the colormap: Default to a nice red/blue thing
    color_map = kwargs.pop('color_map', 'coolwarm')
    assert color_map in plt.colormaps(), "Unknown colormap provided"
    color_gen = plt.get_cmap(color_map)


    #Set up the figure
    figS = plt.figure()

    #Calculate rows for figure size
    num_rows = int(np.ceil(1.0*len(plot_types)/num_cols))

    #Set figure size, including some extra spacing for the colorbar
    #0.1 is the extra space for the colorbar.
    #*1.2 is the extra padding for the axis labels
    #15:1 is the ratio of axis width for regular axes to colorbar axis
    if show_colorbar:
        figS.set_size_inches(fig_size*(num_cols+0.1)*1.2, fig_size*num_rows)

        #Initialize the grid for plotting
        plt_grid = gs.GridSpec(num_rows, num_cols+1, width_ratios=[15]*num_cols+[1])
    else:
        figS.set_size_inches(fig_size*(num_cols)*1.2, fig_size*num_rows)

        #Initialize the grid for plotting
        plt_grid = gs.GridSpec(num_rows, num_cols)

    #Initialize a dictionary of axes corresponding to plot types
    axDict = {}

    #Set up axes and make labels
    for ix, key in enumerate(plot_types):

        iRow = int(ix/num_cols)
        iCol = ix%num_cols

        ax = figS.add_subplot(plt_grid[iRow, iCol])

        if key == 'IQ':
            ax.set_xlabel('I (Volts)')
            ax.set_ylabel('Q (Volts)')

        if key == 'rIQ':
            ax.set_xlabel('Residual of I / $\sigma_\mathrm{I}$')
            ax.set_ylabel('Residual of Q / $\sigma_\mathrm{Q}$')

        if key in ['LogMag', 'LinMag', 'rMag', 'Phase', 'rPhase', 'uPhase',
                    'ruPhase', 'I', 'Q', 'rQ', 'rI']:
            ax.set_xlabel('Frequency (' + freq_units + ')')

        if key == 'LinMag':
            ax.set_ylabel('Magnitude (Volts)')

        if key == 'LogMag':
            ax.set_ylabel('Magnitude (dB)')

        if key == 'rMag':
            ax.set_ylabel('Residual of Magnitude (Volts)')

        if key == 'Phase':
            ax.set_ylabel('Phase (Radians)')

        if key == 'rPhase':
            ax.set_ylabel('Residual of Phase (Radians)')

        if key == 'uPhase':
            ax.set_ylabel('Unwrapped Phase (Radians)')

        if key == 'ruPhase':
            ax.set_ylabel('Residual of unwrapped Phase (Radians)')

        if key == 'I':
            ax.set_ylabel('I (Volts)')

        if key == 'Q':
            ax.set_ylabel('Q (Volts)')

        if key == 'rI':
            ax.set_ylabel('Residual of I / $\sigma_\mathrm{I}$')

        if key == 'rQ':
            ax.set_ylabel('Residual of Q / $\sigma_\mathrm{Q}$')

        #Stuff the axis into the axis dictionary
        axDict[key] = ax

    #Plot the data
    for pwr in powers:
        for temp in temps:
            #Grab the right resonator from the list
            resIndex = indexResList(resList, temp, pwr, itemp=use_itemps)

            #Color magic!
            if color_by == 'temps':
                if len(temps) > 1:
                    plt_color = color_gen(temp*1.0/max(temps))
                else:
                    plt_color = color_gen(0)
            elif color_by == 'pwrs':
                if len(powers) > 1:
                    plt_color = color_gen(1-((max(powers)-pwr)*1.0/(max(powers)-min(powers))))
                else:
                    plt_color = color_gen(0)

            #Not every temp/pwr combo corresponds to a resonator. Ignore missing ones.
            if resIndex is not None:
                res = resList[resIndex]
                scaled_freq = res.freq/unitsDict[freq_units]

                for key, ax in axDict.iteritems():
                    if key == 'IQ':
                        ax.plot(res.I, res.Q, color=plt_color)
                        if plot_fits:
                            ax.plot(res.resultI, res.resultQ, 'k--')

                    if key == 'rIQ':
                        ax.plot(res.residualI, res.residualQ, color=plt_color)

                    if key == 'LogMag':
                        ax.plot(scaled_freq, res.logmag, color=plt_color)
                        if plot_fits:
                            ax.plot(scaled_freq, 20*np.log(res.resultMag), 'k--')

                    if key == 'LinMag':
                        ax.plot(scaled_freq, res.mag, color=plt_color)
                        if plot_fits:
                            ax.plot(scaled_freq, res.resultMag, 'k--')

                    if key == 'rMag':
                        ax.plot(scaled_freq, res.resultMag-res.mag, color=plt_color)

                    if key == 'Phase':
                        if detrend_phase:
                            ax.plot(scaled_freq, sps.detrend(res.phase), color=plt_color)
                            if plot_fits:
                                ax.plot(scaled_freq, sps.detrend(res.resultPhase), 'k--')
                        else:
                            ax.plot(scaled_freq, res.phase, color=plt_color)
                            if plot_fits:
                                ax.plot(scaled_freq, res.resultPhase, 'k--')

                    if key == 'rPhase':
                        ax.plot(scaled_freq, res.resultPhase-res.phase, color=plt_color)

                    if key == 'uPhase':
                        if detrend_phase:
                            ax.plot(scaled_freq, sps.detrend(res.uphase), color=plt_color)
                            if plot_fits:
                                ax.plot(scaled_freq, sps.detrend(np.unwrap(res.resultPhase)), 'k--')
                        else:
                            ax.plot(scaled_freq, res.uphase, color=plt_color)
                            if plot_fits:
                                ax.plot(scaled_freq, np.unwrap(res.resultPhase), 'k--')

                    if key == 'ruPhase':
                        ax.plot(scaled_freq, np.unwrap(res.resultPhase)-res.uphase, color=plt_color)

                    if key == 'I':
                        ax.plot(scaled_freq, res.I, color=plt_color)
                        if plot_fits:
                            ax.plot(scaled_freq, res.resultI, 'k--')

                    if key == 'rI':
                        ax.plot(scaled_freq, res.residualI, color=plt_color)

                    if key == 'Q':
                        ax.plot(scaled_freq, res.Q, color=plt_color)
                        if plot_fits:
                            ax.plot(scaled_freq, res.resultQ, 'k--')

                    if key == 'rQ':
                        ax.plot(scaled_freq, res.residualQ, color=plt_color)

                    ax.set_xticklabels(ax.get_xticks(),rotation=45)

                    if force_square:
                        #Make the plot a square
                        x1, x2 = ax.get_xlim()
                        y1, y2 = ax.get_ylim()

                        #Explicitly passing a float to avoid a warning in matplotlib
                        #when it gets a numpy.float64
                        ax.set_aspect(float((x2-x1)/(y2-y1)))

    #Add the colorbar
    if show_colorbar:
        #Set limits for the min and max colors
        if color_by == 'temps':
            cbar_norm= mpl.colors.Normalize(vmin=0, vmax=max(temps))
            cbar_units = 'Kelvin'
        elif color_by == 'pwrs':
            cbar_norm = mpl.colors.Normalize(vmin=min(powers), vmax=max(powers))
            cbar_units = 'dB'

        #Make an axis that spans all rows for the colorbar
        cax = figS.add_subplot(plt_grid[:, num_cols])

        #Plot and label the colorbar
        cbar_plot = mpl.colorbar.ColorbarBase(cax, cmap=color_gen, norm=cbar_norm)
        cbar_plot.set_label(cbar_units)

    #Clean up the subfigs and make sure nothing overlaps
    figS.tight_layout()

    return figS



def plotResSweepParamsVsTemp(resSweep, plot_keys=None, ignore_keys=None, **kwargs):
    """Plot parameter data vs temperature from a ResonatorSweep object."""

    #This will really only work for sure if block is sucessful
    assert resSweep.smartindex == 'block', "index must be 'block' for plotting to work."
    #TODO: fix for other smartindex types

    #set defaults

    #Which fit data should be plot? lmfit or emcee?
    fitter = kwargs.pop('fitter', 'lmfit')

    #Number of columns
    num_cols = int(kwargs.pop('num_cols', 4))

    #Powers to plot
    powers = list(kwargs.pop('powers', resSweep.pvec))
    assert all(p in resSweep.pvec for p in powers), "Can't plot a power that doesn't exist!"

    #Set up the temperature axis mask
    max_temp = kwargs.pop('max_temp', np.max(resSweep.tvec))
    min_temp = kwargs.pop('min_temp', np.min(resSweep.tvec))

    tempMask = (resSweep.tvec >= min_temp) * (resSweep.tvec <= max_temp)

    if ignore_keys is None:
        ignore_keys = ['listIndex',
                        'temps']
    else:
        assert plot_keys is None, "Either pass plot_keys or ignore_keys, not both."
        assert all(key in resSweep.keys() for key in ignore_keys), "Unknown key"
        ignore_keys.append('listIndex')
        ignore_keys.append('temps')

    fig_size = kwargs.pop('fig_size', 3)

    force_square = kwargs.pop('force_square', False)

    #Set the colormap: Default to a nice red/blue thing
    color_map = kwargs.pop('color_map', 'rainbow')
    assert color_map in plt.colormaps(), "Unknown colormap provided"
    color_gen = plt.get_cmap(color_map)


    #Set up the figure
    figS = plt.figure()

    if plot_keys is None:
        plot_keys = set(resSweep.keys())-set(ignore_keys)
    else:
        assert all(key in resSweep.keys() for key in plot_keys), "Unknown key"

    num_keys = len(plot_keys)

    #Don't need more columns than plots
    if num_keys < num_cols:
        num_cols = num_keys

    #Calculate rows for figure size
    num_rows = int(np.ceil(num_keys/num_cols))

    #Calculate rows for figure size
    num_rows = int(np.ceil(1.0*num_keys/num_cols))

    #Set figure size, including some extra spacing for the colorbar
    figS.set_size_inches(fig_size*(num_cols+0.1)*1.2, fig_size*num_rows)

    #Initialize the grid for plotting
    plt_grid = gs.GridSpec(num_rows, num_cols+1, width_ratios=[15]*num_cols+[1])

    #Loop through all the keys in the ResonatorSweep object and plot them
    for ix, key in enumerate(plot_keys):

        iRow = int(ix/num_cols)
        iCol = ix%num_cols

        axs = figS.add_subplot(plt_grid[iRow, iCol])

        for pwr in powers:
            if len(powers) > 1:
                plt_color = color_gen(1-((max(powers)-pwr)*1.0/(max(powers)-min(powers))))
            else:
                plt_color = color_gen(0)

            axs.plot(resSweep.tvec[tempMask],resSweep[key].loc[tempMask, pwr],'--',color=plt_color, label='Power: '+str(pwr))

        axs.set_xlabel('Temperature (mK)')
        axs.set_ylabel(key)
        axs.set_xticklabels(axs.get_xticks(),rotation=45)

        if force_square:
            #Make the plot a square
            x1, x2 = axs.get_xlim()
            y1, y2 = axs.get_ylim()

            #Explicitly passing a float to avoid an warning in matplotlib
            #when it gets a numpy.float64
            axs.set_aspect(float((x2-x1)/(y2-y1)))

        #Stick some legends where they won't crowd too much
        # if key == 'f0' or key == 'fmin':
        #     axs.legend(loc='best')

    cbar_norm = mpl.colors.Normalize(vmin=min(powers), vmax=max(powers))
    cbar_units = 'dB'

    #Make an axis that spans all rows
    cax = figS.add_subplot(plt_grid[:, num_cols])

    #Plot and label
    cbar_plot = mpl.colorbar.ColorbarBase(cax, cmap=color_gen, norm=cbar_norm)
    cbar_plot.set_label(cbar_units)

    figS.tight_layout()
    return figS

def plotResSweepParamsVsPwr(resSweep, plot_keys=None, ignore_keys=None, **kwargs):
    """Plot parameter data vs power from a ResonatorSweep object."""

    #This will really only work for sure if block is sucessful
    assert resSweep.smartindex == 'block', "index must be 'block' for plotting to work."
    #TODO: fix for other smartindex types

    #set defaults:

    #Which fit data should be plot? lmfit or emcee?
    fitter = kwargs.pop('fitter', 'lmfit')

    #Number of columns
    num_cols = int(kwargs.pop('num_cols', 4))

    #Temperature values to plot
    temps = list(kwargs.pop('temps', resSweep.tvec))
    assert all(t in resSweep.tvec for t in temps), "Can't plot a temperature that doesn't exist!"

    #Set up the power axis mask
    max_power = kwargs.pop('max_power', np.max(resSweep.pvec))
    min_power = kwargs.pop('min_power', np.min(resSweep.pvec))

    pwrMask = (resSweep.pvec >= min_power) * (resSweep.pvec <= max_power)

    fig_size = kwargs.pop('fig_size', 3)

    force_square = kwargs.pop('force_square', False)

    #Set the colormap: Default to a nice red/blue thing
    color_map = kwargs.pop('color_map', 'coolwarm')
    assert color_map in plt.colormaps(), "Unknown colormap provided"
    color_gen = plt.get_cmap(color_map)

    if ignore_keys is None:
        ignore_keys = ['listIndex',
                        'temps']
    else:
        assert plot_keys is None, "Either pass plot_keys or ignore_keys, not both."
        assert all(key in resSweep.keys() for key in ignore_keys), "Unknown key"
        ignore_keys.append('listIndex')
        ignore_keys.append('temps')


    #Set up the figure
    figS = plt.figure()

    if plot_keys is None:
        plot_keys = set(resSweep.keys())-set(ignore_keys)
    else:
        assert all(key in resSweep.keys() for key in plot_keys), "Unknown key"

    num_keys = len(plot_keys)

    #Don't need more columns than plots
    if num_keys < num_cols:
        num_cols = num_keys

    #Calculate rows for figure size
    num_rows = int(np.ceil(1.0*num_keys/num_cols))

    #Set figure size, including some extra spacing for the colorbar
    figS.set_size_inches(fig_size*(num_cols+0.1)*1.2, fig_size*num_rows)

    #Initialize the grid for plotting
    plt_grid = gs.GridSpec(num_rows, num_cols+1, width_ratios=[15]*num_cols+[1])

    #Loop through all the keys in the ResonatorSweep object and plot them
    for ix, key in enumerate(plot_keys):

        iRow = int(ix/num_cols)
        iCol = ix%num_cols

        axs = figS.add_subplot(plt_grid[iRow, iCol])

        for tmp in temps:
            if len(temps) > 1:
                plt_color = color_gen(tmp*1.0/max(temps))
            else:
                plt_color = color_gen(0)

            axs.plot(resSweep.pvec[pwrMask],resSweep[key].loc[tmp,pwrMask],'--', color=plt_color, label='Temperature: '+str(tmp))

        axs.set_xlabel('Power (dB)')
        axs.set_ylabel(key)
        axs.set_xticklabels(axs.get_xticks(),rotation=45)

        if force_square:
            #Make the plot a square
            x1, x2 = axs.get_xlim()
            y1, y2 = axs.get_ylim()

            #Explicitly passing a float to avoid an warning in matplotlib
            #when it gets a numpy.float64
            axs.set_aspect(float((x2-x1)/(y2-y1)))

        #Stick some legends where they won't crowd too much
        # if key == 'f0' or key == 'fmin':
        #     axs.legend(loc='best')
    #Make an axis that spans all rows
    cax = figS.add_subplot(plt_grid[:, num_cols])

    #Set colorbar limits
    cbar_norm= mpl.colors.Normalize(vmin=0, vmax=max(temps))
    cbar_units = 'mK'

    #Plot and label
    cbar_plot = mpl.colorbar.ColorbarBase(cax, cmap=color_gen, norm=cbar_norm)
    cbar_plot.set_label(cbar_units)

    figS.tight_layout()
    return figS
