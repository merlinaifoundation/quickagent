import sys
import numpy as np
from PyQt5 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg
import sounddevice as sd
import soundfile as sf

class AudioVisualizer(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.audio_file = None
        self.audio_data = None
        self.sample_rate = None
        self.is_playing = False
        self.current_frame = 0

        self.init_ui()

    def init_ui(self):
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        layout = QtWidgets.QVBoxLayout(central_widget)

        # File selection button
        self.file_button = QtWidgets.QPushButton("Select Audio File")
        self.file_button.clicked.connect(self.select_file)
        layout.addWidget(self.file_button)

        # Play/Stop button
        self.play_button = QtWidgets.QPushButton("Play")
        self.play_button.clicked.connect(self.toggle_playback)
        self.play_button.setEnabled(False)
        layout.addWidget(self.play_button)

        # Graph widget
        self.graph_widget = pg.PlotWidget()
        layout.addWidget(self.graph_widget)

        self.line = self.graph_widget.plot(np.arange(1024), np.zeros(1024))

        # Timer for updates
        self.timer = QtCore.QTimer()
        self.timer.setInterval(30)  # 30ms = ~33 fps
        self.timer.timeout.connect(self.update_plot)

        self.setGeometry(300, 300, 600, 400)
        self.setWindowTitle('Audio Visualizer')
        self.show()

    def select_file(self):
        file_dialog = QtWidgets.QFileDialog()
        self.audio_file, _ = file_dialog.getOpenFileName(self, "Select Audio File", "", "Audio Files (*.wav *.mp3)")
        if self.audio_file:
            self.audio_data, self.sample_rate = sf.read(self.audio_file, dtype='float32')
            self.play_button.setEnabled(True)
            self.current_frame = 0
            self.is_playing = False
            self.play_button.setText("Play")

    def toggle_playback(self):
        if self.is_playing:
            sd.stop()
            self.timer.stop()
            self.is_playing = False
            self.play_button.setText("Play")
        else:
            sd.play(self.audio_data[self.current_frame:], self.sample_rate)
            self.timer.start()
            self.is_playing = True
            self.play_button.setText("Stop")

    def update_plot(self):
        if self.current_frame < len(self.audio_data):
            chunk = self.audio_data[self.current_frame:self.current_frame + 1024]
            self.line.setData(np.arange(len(chunk)), chunk)
            self.current_frame += 1024
        else:
            self.toggle_playback()  # Stop playback when the end is reached

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main = AudioVisualizer()
    sys.exit(app.exec_())