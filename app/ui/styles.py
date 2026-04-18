MAIN_WINDOW_STYLE = """
QMainWindow {
    background-color: #121417;
    color: #E6EAF0;
    font-size: 14px;
}

QWidget {
    color: #E6EAF0;
    font-size: 14px;
    background: transparent;
}


QGroupBox {
    background-color: #1A1F26;
    border: 1px solid #2A313B;
    border-radius: 12px;
    margin-top: 12px;
    padding: 12px;
    font-weight: 600;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
    color: #DDE5F0;
}

QLabel {
    color: #E6EAF0;
    background: transparent;
}

QLabel#videoLabel {
    background-color: #0B0E12;
    border: 1px solid #2A313B;
    border-radius: 14px;
    color: #8E99A8;
    font-size: 18px;
}

QPushButton {
    background-color: #2B6BE4;
    color: white;
    border: none;
    border-radius: 10px;
    padding: 10px 14px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #3A78EC;
}

QPushButton:pressed {
    background-color: #2359C0;
}

QPushButton:disabled {
    background-color: #3A404A;
    color: #9199A6;
}

QSlider::groove:horizontal {
    border: none;
    height: 6px;
    background: #2A313B;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #2B6BE4;
    width: 16px;
    margin: -5px 0;
    border-radius: 8px;
}

QSpinBox {
    background-color: #11161C;
    border: 1px solid #2A313B;
    border-radius: 8px;
    padding: 6px;
    color: #E6EAF0;
}

QCheckBox {
    spacing: 8px;
    padding: 4px 2px;
    color: #E6EAF0;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
}

QCheckBox::indicator:unchecked {
    border: 1px solid #4A5563;
    background: #11161C;
    border-radius: 4px;
}

QCheckBox::indicator:checked {
    border: 1px solid #2B6BE4;
    background: #2B6BE4;
    border-radius: 4px;
}

QScrollArea {
    border: none;
    background: transparent;
}
"""
