import numpy as np
import matplotlib.pyplot as plt
import scipy.signal as sig
from scipy.interpolate import interp1d
import pdb

# BandPass Filter
def BandPass(S, SmpRate, lowcut, highcut):
    N = S.shape[0]
    Sfft = np.fft.rfft(S) / N
    freqs = np.linspace(0, SmpRate / 2, N / 2 + 1)
    Sfft[freqs < lowcut] = 0
    Sfft[freqs > highcut] = 0

    SBandPass = np.fft.irfft(Sfft*N)
    return SBandPass

def heart_rate(time, filteredData) -> (np.array, np.array):
    # 50 samples per second, a peak every 50 samples = 1 hz
    peakTime = time[sig.argrelmax(filteredData, order=25)]
    # sig.argrelmax(filteredData,order = 25)
    #indexes value of peak time, stored in a tuple(numpy array, )

    # calculate the heartrate given time between two peaks
    # = 60 (seconds / minute) / (seconds / beat) = (beats / minute)
    return np.column_stack((peakTime[:-1], (60 / (peakTime[1:] - peakTime[:-1]))))

def respiration(time, filteredData) -> (np.array, np.array):
    peakTime = time[sig.argrelmax(filteredData, order=25)]
    return np.column_stack((peakTime[:-1], (60 / (peakTime[1:] - peakTime[:-1]))))

def spo2(time, IR_filt, RED_filt, order):

    peakIR = IR_filt[sig.argrelmax(IR_filt, order=order)]
    peakTime = time[sig.argrelmax(IR_filt, order=order)]
    minPeakTime = time[sig.argrelmin(IR_filt, order=order)]
    interpldPoint = interp1d(minPeakTime, IR_filt[sig.argrelmin(IR_filt, order=order)])

    DCIR = interpldPoint(peakTime[1:])
    ACIR = peakIR[1:] - DCIR

    peakRED = RED_filt[sig.argrelmax(RED_filt, order=order)]
    peakTimeRED = time[sig.argrelmax(RED_filt, order=order)]
    minPeakTimeRED = time[sig.argrelmin(RED_filt, order=order)]
    interpldPoint = interp1d(minPeakTimeRED, RED_filt[sig.argrelmin(RED_filt, order=order)])

    DCRED = interpldPoint(peakTimeRED[1:])
    ACRED = peakRED[1:] - DCRED

    R = (ACRED * DCIR) / (ACIR * DCRED)
    spo2 = (R*R*(-45.06))+(R*30.354) + 94.845
    
    return np.column_stack((peakTime[:-1],spo2))

def expand_data(time, calculated_rate):
    out = np.empty((time.shape[0], calculated_rate.shape[1]))
    out[:,0] = time
    for i in range(calculated_rate.shape[0]-1):
        locations = np.where(
                np.all([(calculated_rate[i, 0] <= time),(time < calculated_rate[i+1,0])], axis=0))
        out[locations, 1] = calculated_rate[i, 1]
    out[np.where(time < calculated_rate[0,0]), 1] = calculated_rate[0, 1]
    out[np.where(time >= calculated_rate[-1,0]), 1] = calculated_rate[-1, 1]
    return out[:,1:]

def write_file(data, fname = 'foo.txt'):
    with open(fname,'w') as f:
        for row in data:
            f.write(', '.join(map(str, row)))
            f.write('\n')

def plot_rates(calculated_rates):
    time = calculated_rates[:,0]
    HR = calculated_rates[:,1]
    RS = calculated_rates[:,2]
    SP = calculated_rates[:,3]
    plt.figure()
    f1, = plt.plot(time, HR, label='heart')
    f2, = plt.plot(time, RS, label='respiration')
    f3, = plt.plot(time, SP, label='spo2')
    plt.legend((f1, f2, f3),
                ('heart', 'respiration', 'spO2'))
    plt.show(False)
    
def plot_signal(time, IR, RED):
    plt.figure()
    plt.clf()
    plt.plot(time, RED, label='RED')
    plt.plot(time, IR, label='IR')

    plt.xlabel('Time (Seconds)')
    plt.grid(True)
    plt.axis('tight')
    plt.legend(loc='upper left')
    plt.show(False)

def plot_FFT(time, signal, lowcut, highcut):
    N = signal.shape[0]
    W = np.linspace(0, SmpRate / 2, N / 2 + 1)
    fft_signal = np.fft.rfft(signal) / N
    cut_signal = np.array(fft_signal)
    cut_signal[W<lowcut] = 0
    cut_signal[W>highcut] = 0
    filtered_signal = np.fft.irfft(cut_signal)
    
    plt.figure()
    plt.subplot()
    plt.plot(time[:signal.size], (signal - np.mean(signal))/ N + np.mean(filtered_signal), label='Raw signal')

    plt.plot(time[:filtered_signal.size], filtered_signal, label='Filtered')

    plt.xlabel('Time (Seconds)')
    plt.grid(True)
    plt.axis('tight')
    plt.legend(loc='upper left')

    plt.figure()
    plt.plot(W, fft_signal, label='FFT IR')
    plt.plot(W, cut_signal, label='CUT FFT IR')
    axes = plt.gca()
    axes.set_ylim((-fft_signal.mean(), fft_signal.mean()))

    plt.show(block=False)

if __name__ == '__main__':
    data = np.genfromtxt("sensor.csv",
                         delimiter=',', skip_header=1, usecols=(0, 1, 2, 3, 4), invalid_raise=True)
    np.set_printoptions(precision=3, suppress=True)
    SECONDS_OF_DATA=600
    time = np.linspace(0, SECONDS_OF_DATA, data.shape[0]) 
    IR = data[:, -2]
    RED = data[:, -1]

    SmpRate= len(data) / SECONDS_OF_DATA

    HEART_LOW = 0.9
    HEART_HIGH = 3

    #plot_FFT(time, RED, HEART_LOW, HEART_HIGH)
    IR_filt = BandPass(IR, SmpRate, HEART_LOW, HEART_HIGH)
    RED_filt = BandPass(RED, SmpRate, HEART_LOW, HEART_HIGH)
    calculated_HR = heart_rate(time, RED_filt)

    RESP_LOW = 0.16
    RESP_HIGH = 0.33

    #plot_FFT(time, RED, RESP_LOW, RESP_HIGH)
    IR_filt = BandPass(IR, SmpRate, RESP_LOW, RESP_HIGH)
    RED_filt = BandPass(RED, SmpRate, RESP_LOW, RESP_HIGH)
    calculated_RS = respiration(time,RED_filt)

    SPO2_LOW = 1
    SPO2_HIGH = 2
    IR_filt = BandPass(IR, SmpRate, SPO2_LOW, SPO2_HIGH)
    RED_filt = BandPass(RED, SmpRate, SPO2_LOW, SPO2_HIGH)
    #plot_FFT(time, IR, SPO2_LOW, SPO2_HIGH)
    #plot_FFT(time, RED, SPO2_LOW, SPO2_HIGH)
    calculated_SP = spo2(time, IR, RED, 10)

    calculated_rates = np.concatenate((time[:,np.newaxis], 
                        expand_data(time, calculated_HR),
                        expand_data(time, calculated_RS),
                        expand_data(time, calculated_SP)),
                        axis = 1)
    #write_file(calculated_rates, 'hw6_data.csv')
    plot_rates(calculated_rates)
