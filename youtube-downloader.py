from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, \
    QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QIcon, QMovie
from pytube import YouTube
import sys
import os
from os import path

__author__ = "Yamil Iran Garcia"
__status__ = "Initial Release"
__version__ = "1.0"
__date__ = "13 Sept. 2022"
__license__ = "Python Software Foundation License (PSFL)"


class DownloadThread(QThread):
    """
    DownloadThread is a class used as a secondary thread of execution to
    offload long-running tasks (download video from YouTube) from the main
    thread and prevent GUI freezing.
    PyQt graphical user interface (GUI) applications have a main thread of
    execution that runs the event loop and GUI. If a long-running task is
    launched in this thread, then the GUI will be frozen until the task
    terminates.
    """
    # Signal emitted when the download has finished.
    download_finished = pyqtSignal(str)
    # Signal emitted to indicate the progress.
    progress = pyqtSignal(float)

    def __init__(self, url: str, dir_name: str = None) -> None:
        """
        Constructor function for this class.
        :param url: YouTube video url.
        :param dir_name: Directory where to save the video file.
        """
        super(DownloadThread, self).__init__()

        # Instance attributes.
        self.url = url
        self.dir_name = dir_name
        self.download_progress_percent = 0
        self.file_size = 0

    def run(self) -> None:
        """
        Starting point for the thread. After calling start(),
        the newly created thread calls this function.
        :return: None
        """
        # Create an instance of YouTube class.
        youtube = YouTube(self.url,
                          on_progress_callback=self.on_progress,
                          on_complete_callback=self.on_complete)
        # Get the highest resolution stream that is a progressive
        # video.
        stream = youtube.streams.get_highest_resolution()
        # Get the file size.
        self.file_size = stream.filesize
        # Download the YouTube video.
        if self.dir_name is not None:
            stream.download(self.dir_name)
        else:
            stream.download()

    def on_progress(self, stream, chunk, remaining) -> None:
        """
        User defined callback function for stream download
        progress events. The on_progress_callback function will
        run whenever a chunk is downloaded from a video.
        :param stream: Video stream.
        :param chunk: Downloaded data chunk.
        :param remaining: Remaining data.
        :return: None.
        """
        self.download_progress_percent = (100 * (self.file_size - remaining)) / self.file_size
        print("Download Progress: {:00.0f}%".format(self.download_progress_percent))
        self.progress.emit(self.download_progress_percent)

    def on_complete(self, stream, path_to_file: str) -> None:
        """
        User defined callback function for stream download
        complete events. The on_complete_callback function will run
        after a video has been fully downloaded.
        :param stream: Video stream.
        :param path_to_file: Directory where downloaded video
               was saved.
        :return: None.
        """
        print("Video download was completed, and saved at: \n{0}".format(path_to_file))
        self.download_finished.emit(path_to_file)


class MainWindow(QMainWindow):
    """
    MainWindow is a class designed to build a graphical user
    interface (GUI) using the PyQt framework.
    """
    def __init__(self) -> None:
        super(MainWindow, self).__init__()

        # Instance attributes.
        # GUI elements.
        self.url_label = QLabel()
        self.url_line_edit = QLineEdit()
        self.download_button = QPushButton()
        self.download_button.clicked.connect(self.download_video)
        self.spinner = QLabel(self)
        self.movie = QMovie()
        self.url: str = ""
        # Label used to show messages in the Status Bar.
        self.status_bar_msg_label = QLabel("")
        # Create a secondary thread of execution to offload
        # the task to download the video, which is a long-running task.
        self.download_thread = None
        # Set-up thr GUI.
        self.setup_gui()

    def setup_gui(self) -> None:
        """
        Convenience function designed to set-up the
        GUI elements.
        :return: None
        """
        self.url_label.setText("Enter URL")
        self.url_line_edit.setToolTip("Enter YouTube video url.")
        self.download_button.setText("Download")
        self.download_button.setToolTip("Click to download Youtube Video.")
        url_horizontal_layout = QHBoxLayout()
        url_horizontal_layout.addWidget(self.url_label)
        url_horizontal_layout.addWidget(self.url_line_edit)
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(self.download_button)
        # Set up a spinner to show when video is being
        # downloaded.
        self.spinner.setContentsMargins(0, 0, 0, 0)
        self.spinner.setAlignment(Qt.AlignCenter)
        file_name = os.path.dirname(os.path.realpath(__file__)) + "\\Dual Ring-1s-60px.gif"
        if path.exists(file_name):
            self.movie.setFileName(file_name)
            self.spinner.setMovie(self.movie)
            self.spinner.hide()
        # Create a Vertical layout instance.
        vertical_layout = QVBoxLayout()
        vertical_layout.addLayout(url_horizontal_layout)
        vertical_layout.addLayout(button_layout)
        vertical_layout.addWidget(self.spinner, alignment=Qt.AlignTop)
        vertical_layout.addStretch(1)
        # Create the central widget.
        widget = QWidget(self)
        widget.setLayout(vertical_layout)
        # Set the central widget.
        self.setCentralWidget(widget)
        self.setFixedSize(600, 90)  # height with spinner = 150
        # Set the window icon.
        file_name = os.path.dirname(os.path.realpath(__file__)) + "\\youtube_icon.ico"
        if path.exists(file_name):
            self.setWindowIcon(QIcon(file_name))
        # Set window title.
        self.setWindowTitle("YouTube Downloader")
        # Create and add the status bar to the window.
        self.create_status_bar()

    @pyqtSlot()
    def download_video(self) -> None:
        """
        Convenience function to create a thread to download
        a YouTube video.
        :return:
        """
        # If the text of the line edit is not empty.
        if len(self.url_line_edit.text()) > 0:
            # Ask the user to select the directory
            # where the downloaded file will be saved.
            dir_name = self.get_dir()
            # Resize the window to adjust its height
            # to fit the spinner.
            self.setFixedSize(600, 150)
            self.resize(600, 150)
            # Get the text of the line edit.
            self.url = self.url_line_edit.text()
            # Create a secondary thread of execution to offload
            # the task to download the video, which is a long-running task.
            self.download_thread = DownloadThread(self.url, dir_name)
            self.download_thread.progress.connect(lambda progress: self.on_progress(progress))
            self.download_thread.download_finished.connect(lambda path_to_file: self.on_finished(path_to_file))
            self.download_thread.start()
            # Show the spinner.
            self.spinner.show()
            # Start the spinner.
            self.movie.start()
            # Show message in the status bar.
            self.status_bar_msg_label.setText("Wait...")
        else:
            # Show message in the status bar.
            self.status_bar_msg_label.setText("Please, enter a YouTube url in the Line Edit. ")

    @pyqtSlot()
    def on_finished(self, path_to_file: str) -> None:
        """
        Function or Qt slot called when the video download
        has completed.
        :param path_to_file: Directory where downloaded video
                             was saved.
        :return: None.
        """
        # Stop the spinner.
        self.movie.stop()
        # Hide the spinner.
        self.spinner.hide()
        # Resize the window to adjust its height
        # without the spinner.
        self.setFixedSize(600, 90)
        self.resize(600, 90)
        # Show message in the status bar.
        self.status_bar_msg_label.setText("Saved at {0} ".format(path_to_file))
        # Show a message using a modal window.
        self.messageBox("File Location",
                        "The video was saved at:\n\n{0}".format(path_to_file),
                        QMessageBox.NoIcon)

    @pyqtSlot()
    def on_progress(self, progress: float) -> None:
        """
        Function or Qt slot called every time a new chunk of data
        has being downloaded.
        :param progress: Downloaded data chunk.
        :return: None.
        """
        # Show message in the status bar.
        self.status_bar_msg_label.setText("Download Progress: {:00.0f}%".format(progress))

    def get_dir(self) -> str:
        """
        This is a convenience function that will return an existing
        directory selected by the user.
        :return: The user selected directory or current directory.
        """
        # Get current directory.
        current_directory = os.path.dirname(os.path.realpath(__file__))
        # Get an existing directory selected by the user.
        dir_name = QFileDialog.getExistingDirectory(self,
                                                    "Select the directory to save the file.",
                                                    current_directory,
                                                    QFileDialog.ShowDirsOnly)
        # If dir_name is not empty.
        if len(dir_name) > 0:
            return dir_name
        return current_directory

    def create_status_bar(self) -> None:
        """
        This is a convenience function designed to
        create a custom status bar for the window.
        :return: None.
        """
        # Create a spare label to use it as a spacer.
        spare_label = QLabel("")
        # Create a label to show the software revision in the status bar.
        revision_label = QLabel("Ver: {0}".format(__version__))
        # Add labels to the QMainWindow status bar.
        self.statusBar().addWidget(self.status_bar_msg_label)
        self.statusBar().addWidget(spare_label, stretch=20)
        self.statusBar().addWidget(revision_label)

    def messageBox(self, title: str, message: str, icon: int) -> None:
        """
        Create a modal dialog to notify the user about an event.
        It can be an error, or an information, or a warning.
        :param title: Title for this dialog window.
        :param message: Message to shown to user.
        :param icon: Icon shown, must be: QMessageBox::NoIcon, QMessageBox.Information,
                     QMessageBox.Warning, QMessageBox.Critical
        :return: None
        """
        # Create an instance of the QMessageBox class to create a message window.
        msg_box = QMessageBox(self)
        msg_box.setIcon(icon)
        msg_box.setText(message)
        msg_box.setWindowTitle(title)
        msg_box.setStandardButtons(QMessageBox.Ok)
        return_value = msg_box.exec()
        if return_value == QMessageBox.Ok:
            pass


if __name__ == '__main__':
    # Create a QApplication object. It manages the GUI application's control
    # flow and main settings. It handles widget specific initialization,
    # finalization. For any GUI application using Qt, there is precisely
    # one QApplication object
    app = QApplication(sys.argv)
    # Create an instance of the class MainWindow.
    # window = MainWindow(sys.argv)
    window = MainWindow()
    # Show the window.
    window.show()
    # Start Qt event loop.
    sys.exit(app.exec_())
