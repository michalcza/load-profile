#include <QApplication>
#include <QFileDialog>
#include <QMessageBox>
#include <QDebug>
#include <QMainWindow>
#include <QWidget>
#include <QPushButton>

#include <iostream>
#include <fstream>
#include <string>
#include <stdexcept>

#include <pandas.h>  // Assuming Pandas (or a similar library) is used for CSV processing.

// Function to process the CSV file (same as your original logic)
void process_csv(const std::string& input_file) {
    try {
        std::cout << "Processing file: " << input_file << std::endl;
        // Your existing CSV processing code here...
        // (Replace with your Pandas processing logic or whatever library you're using)
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
    }
}

class MainWindow : public QMainWindow {
    Q_OBJECT

public:
    MainWindow(QWidget* parent = nullptr) : QMainWindow(parent) {
        resize(300, 100);

        QPushButton* selectFileButton = new QPushButton("Select CSV File", this);
        selectFileButton->setGeometry(50, 20, 200, 50);

        // Connect button click to file selection dialog
        connect(selectFileButton, &QPushButton::clicked, this, &MainWindow::onSelectFile);
    }

private slots:
    void onSelectFile() {
        QString fileName = QFileDialog::getOpenFileName(this, "Open CSV File", "", "CSV Files (*.csv)");

        if (fileName.isEmpty()) {
            QMessageBox::warning(this, "No File Selected", "Please select a valid CSV file.");
        } else {
            qDebug() << "Selected file:" << fileName;
            process_csv(fileName.toStdString());  // Call the function to process the selected CSV file
        }
    }
};

int main(int argc, char *argv[]) {
    QApplication app(argc, argv);

    MainWindow window;
    window.show();

    return app.exec();
}
