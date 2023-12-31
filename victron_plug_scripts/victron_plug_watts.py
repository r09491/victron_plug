#!/usr/bin/env python3

import sys
import argparse
import pandas as pd
import numpy as np

from datetime import datetime, timedelta


V_SAMPLES = 60 # 2 hour
V_LOAD_OFF = 12.1 # V
V_LOAD_DISCHARGE = 12.8 #V


def strip_unit(value):
    return float(value[:-1])


def estimate_load_off(f = sys.stdin):
    sep = '\t'
    names = 'TIME,VPV,IPV,PPV,V,I,P,IL,PL'.split(',')
    df = pd.read_csv(f, sep = sep, names = names).tail(V_SAMPLES)

    vdf = df.loc[:,['TIME','V', 'PL', 'PPV', 'P']]

    """ The timestamps """
    t = np.array(vdf.TIME)
    
    """ The battery voltage samples """
    v = np.array(vdf.V.apply(strip_unit))

    samples = len(v)

    """ The power samples """
    pl = np.array(vdf.PL.apply(strip_unit))
    p = np.array(vdf.P.apply(strip_unit))
    ppv = np.array(vdf.PPV.apply(strip_unit))

    """ Calculate the means over the last hour """
    pl_mean = np.mean(pl[int(samples/2):])
    p_mean = np.mean(p[int(samples/2):])
    ppv_mean = np.mean(ppv[int(samples/2):])

    text = f'TIME {t[-1]}'
    text += f' SOLAR {ppv_mean:.1f} W'
    text += f' BAT {p_mean:+.1f} W'
    text += f' LOAD {pl_mean:.1f} W'
    text += f' SYS {-ppv_mean + p_mean + pl_mean:.1f} W'
    text += f' V {v[-1]:.2f} V'    

    if v[0] > v[-1] and v[0] < V_LOAD_DISCHARGE and samples >= V_SAMPLES:
        
        """ Forecast LOAD OFF time for discharge

        Graphical plot of discharge shows exponential behaviour y = a * b**x

        As per setup there are samples for one hour. This result in: a = v[0], b = v[-1]/v[0]

        The hours to load off can then be determined by the below equation

        """

        load_off_hours = (np.log(V_LOAD_OFF) - np.log(v[0])) / (np.log(v[-1]) -np.log(v[0]))        
        load_off_hours -= 1.0
        text += f' LOAD OFF {load_off_hours:.1f} h'

        if load_off_hours < 24 :
            load_off_time = datetime.strptime(t[-1], "%H:%M") + \
                timedelta(minutes = int(load_off_hours * 60))
            text += f' @ {load_off_time.strftime("%H:%M")}'

    print(text)

    return 0


def parse_args():
    parser = argparse.ArgumentParser(description='Esimate MPPT load off time')

    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    estimate_load_off()
    return 0

if __name__ == '__main__':
    sys.exit(main())
