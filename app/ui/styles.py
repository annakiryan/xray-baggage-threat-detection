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

/* Только navigation rail */
QWidget#navigationRail {
    background-color: #181818;
    border-right: 1px solid #2A313B;
}

QToolButton {
    background: transparent;
    border: none;
    border-left: 2px solid transparent;
    border-radius: 0px;
    padding: 0px;
}

QToolButton:hover {
    background-color: #2A313B;
}

QToolButton:checked {
    background-color: #1F2630;
    border-left: 2px solid #E6EAF0;
}

QToolTip {
    background-color: #1A1F26;
    color: #E6EAF0;
    border: 1px solid #2A313B;
    padding: 4px 8px;
}
"""

SESSION_HISTORY_STYLE = """
QWidget#historyPageRoot {
    background-color: #121417;
}

QWidget#historyPageRoot QLabel {
    color: #E6EAF0;
    font-size: 14px;
    background: transparent;
}

QWidget#historyPageRoot QGroupBox {
    background-color: #1A1F26;
    border: 1px solid #2A313B;
    border-radius: 12px;
    margin-top: 12px;
    padding: 10px;
    font-weight: 600;
}

QWidget#historyPageRoot QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
    color: #DDE5F0;
}

QWidget#historyPageRoot QLabel#historyViewerTitle {
    color: #DDE5F0;
    font-size: 18px;
    font-weight: 700;
}

QWidget#historyPageRoot QLabel#imageViewer {
    background-color: #0B0E12;
    border: 1px solid #2A313B;
    border-radius: 12px;
    color: #8E99A8;
    font-size: 16px;
}

QWidget#historyPageRoot QLabel#summaryCaption {
    color: #9EABB9;
    font-size: 13px;
    font-weight: 500;
}

QWidget#historyPageRoot QLabel#summarySectionTitle {
    color: #DDE5F0;
    font-size: 14px;
    font-weight: 600;
    margin-top: 4px;
}

QWidget#historyPageRoot QFrame#statCard {
    background-color: #11161C;
    border: 1px solid #2A313B;
    border-radius: 12px;
}

QWidget#historyPageRoot QLabel#statCardTitle {
    color: #9EABB9;
    font-size: 13px;
    font-weight: 500;
}

QWidget#historyPageRoot QLabel#statCardValue {
    color: #E6EAF0;
    font-size: 22px;
    font-weight: 700;
}

QWidget#historyPageRoot QTextEdit#summaryTextBlock {
    background-color: #11161C;
    border: 1px solid #2A313B;
    border-radius: 10px;
    padding: 8px;
    color: #E6EAF0;
}

QWidget#historyPageRoot QListWidget,
QWidget#historyPageRoot QTreeWidget {
    background-color: #11161C;
    border: 1px solid #2A313B;
    border-radius: 10px;
    outline: none;
    padding: 4px;
}

QWidget#historyPageRoot QListWidget::item,
QWidget#historyPageRoot QTreeWidget::item {
    padding: 8px;
    border-radius: 6px;
}

QWidget#historyPageRoot QListWidget::item:selected,
QWidget#historyPageRoot QTreeWidget::item:selected {
    background-color: #2B6BE4;
    color: white;
}

QWidget#historyPageRoot QListWidget::item:hover,
QWidget#historyPageRoot QTreeWidget::item:hover {
    background-color: #1E2630;
}

QWidget#historyPageRoot QHeaderView::section {
    background-color: #11161C;
    color: #9EABB9;
    border: none;
    padding: 6px;
    font-weight: 600;
}
"""