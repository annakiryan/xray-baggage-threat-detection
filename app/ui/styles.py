def build_main_window_style(
    palette: dict,
    ui_scale: int = 100,
) -> str:
    values = _build_style_values(palette, ui_scale)
    return MAIN_WINDOW_STYLE.format(**values)


def build_session_history_style(
    palette: dict,
    ui_scale: int = 100,
) -> str:
    values = _build_style_values(palette, ui_scale)
    return SESSION_HISTORY_STYLE.format(**values)


def _build_style_values(palette: dict, ui_scale: int) -> dict:
    values = dict(palette)
    scale = ui_scale / 100

    values.update(
        {
            "font_small": _scaled(12, scale),
            "font_caption": _scaled(13, scale),
            "font_base": _scaled(14, scale),
            "font_medium": _scaled(15, scale),
            "font_section": _scaled(16, scale),
            "font_large": _scaled(18, scale),
            "font_icon": _scaled(22, scale),
            "font_button_big": _scaled(24, scale),
            "font_page_title": _scaled(30, scale),
            "group_padding": _scaled(12, scale),
            "button_padding_y": _scaled(10, scale),
            "button_padding_x": _scaled(14, scale),
            "input_padding_y": _scaled(10, scale),
            "input_padding_x": _scaled(12, scale),
            "tab_padding_y": _scaled(9, scale),
            "tab_padding_x": _scaled(14, scale),
            "slider_height": _scaled(6, scale),
            "slider_radius": _scaled(3, scale),
            "slider_handle_width": _scaled(16, scale),
            "slider_handle_radius": _scaled(8, scale),
            "slider_handle_margin": _scaled(-5, scale),
            "checkbox_size": _scaled(16, scale),
            "scrollbar_size": _scaled(8, scale),
            "scrollbar_min_handle": _scaled(28, scale),
            "card_check_size": _scaled(24, scale),
            "combo_min_width": _scaled(160, scale),
            "combo_drop_width": _scaled(28, scale),
        }
    )

    return values


def _scaled(value: int, scale: float) -> int:
    if value < 0:
        return min(-1, round(value * scale))

    return max(1, round(value * scale))


MAIN_WINDOW_STYLE = """
QMainWindow {{
    background-color: {bg_main};
    color: {text};
    font-size: {font_base}px;
}}

QWidget {{
    color: {text};
    font-size: {font_base}px;
    background: transparent;
}}

QWidget#mainCentralWidget,
QWidget#settingsPageRoot {{
    background-color: {bg_main};
}}

QLabel {{
    color: {text};
    background: transparent;
}}

QGroupBox {{
    background-color: {bg_card};
    border: 1px solid {border};
    border-radius: 12px;
    margin-top: 12px;
    padding: {group_padding}px;
    font-weight: 600;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
    color: {title};
}}

QLabel#videoLabel {{
    background-color: {bg_card};
    border: 1px solid {border};
    border-radius: 14px;
    color: {text_muted};
    font-size: {font_large}px;
}}

QPushButton {{
    background-color: {accent};
    color: white;
    border: none;
    border-radius: 10px;
    padding: {button_padding_y}px {button_padding_x}px;
    font-weight: 600;
}}

QPushButton:hover {{
    background-color: {accent_hover};
}}

QPushButton:pressed {{
    background-color: {accent_pressed};
}}

QPushButton:disabled {{
    background-color: #3A404A;
    color: #9199A6;
}}

QSlider::groove:horizontal {{
    border: none;
    height: {slider_height}px;
    background: {border};
    border-radius: {slider_radius}px;
}}

QSlider::handle:horizontal {{
    background: {accent};
    width: {slider_handle_width}px;
    margin: {slider_handle_margin}px 0;
    border-radius: {slider_handle_radius}px;
}}

QCheckBox {{
    spacing: 8px;
    padding: 4px 2px;
    color: {text};
}}

QCheckBox::indicator {{
    width: {checkbox_size}px;
    height: {checkbox_size}px;
}}

QCheckBox::indicator:unchecked {{
    border: 1px solid #4A5563;
    background: {bg_inner};
    border-radius: 4px;
}}

QCheckBox::indicator:checked {{
    border: 1px solid {accent};
    background: {accent};
    border-radius: 4px;
}}

QWidget#navigationRail {{
    background-color: #181818;
    border-right: 1px solid {border};
}}

QToolButton {{
    background: transparent;
    border: none;
    border-left: 2px solid transparent;
    border-radius: 0px;
    padding: 0px;
}}

QToolButton:hover {{
    background-color: {border};
}}

QToolButton:checked {{
    border-left: 2px solid {text};
}}

QToolTip {{
    background-color: {bg_inner};
    color: {text};
    border: 1px solid {border};
    padding: 4px 8px;
}}

QScrollArea {{
    border: none;
    background: transparent;
}}

QScrollBar:vertical {{
    background: transparent;
    width: {scrollbar_size}px;
    margin: 4px 0 4px 0;
}}

QScrollBar::handle:vertical {{
    background: #3A4655;
    border-radius: 4px;
    min-height: {scrollbar_min_handle}px;
}}

QScrollBar::handle:vertical:hover {{
    background: #4A5A6D;
}}

QScrollBar::handle:vertical:pressed {{
    background: {accent};
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0px;
    background: transparent;
}}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {{
    background: transparent;
}}

QLabel#settingsPageTitle {{
    color: {title};
    font-size: {font_page_title}px;
    font-weight: 700;
}}

QLabel#settingsPageSubtitle {{
    color: {text_muted};
    font-size: {font_section}px;
}}

QFrame#settingsRow {{
    background-color: {bg_card};
    border: 1px solid {border};
    border-radius: 12px;
}}

QLabel#settingsIcon {{
    color: {text_muted};
    font-size: {font_icon}px;
    font-weight: 700;
}}

QLabel#settingsRowTitle {{
    color: {title};
    font-size: {font_section}px;
    font-weight: 700;
}}

QLabel#settingsRowSubtitle {{
    color: {text_muted};
    font-size: {font_caption}px;
}}

QPushButton#themeCard,
QPushButton#colorCard,
QPushButton#thicknessButton {{
    background-color: {bg_inner};
    border: 1px solid {border};
    border-radius: 10px;
    padding: 0px;
}}

QPushButton#themeCard {{
    text-align: left;
}}

QPushButton#themeCard:hover,
QPushButton#colorCard:hover,
QPushButton#thicknessButton:hover {{
    border: 1px solid {accent_hover};
}}

QPushButton#themeCard:checked,
QPushButton#colorCard:checked,
QPushButton#thicknessButton:checked {{
    border: 2px solid {accent};
    background-color: {bg_inner};
}}

QLabel#themeCardTitle {{
    color: {title};
    font-size: {font_base}px;
    font-weight: 700;
}}

QLabel#themeCardSubtitle,
QLabel#colorCardSubtitle {{
    color: {text_muted};
    font-size: {font_small}px;
}}

QLabel#colorCardTitle {{
    color: {title};
    font-size: {font_medium}px;
    font-weight: 700;
}}

QLabel#cardCheck {{
    background-color: {accent};
    color: white;
    border-radius: 12px;
    font-size: {font_base}px;
    font-weight: 700;
    min-width: {card_check_size}px;
    min-height: {card_check_size}px;
    max-width: {card_check_size}px;
    max-height: {card_check_size}px;
}}

QLabel#sliderTickLabel {{
    color: {title};
    font-size: {font_base}px;
    font-weight: 600;
}}

QLabel#colorPreview {{
    border-radius: 6px;
}}

QFrame#thicknessPreview {{
    background: transparent;
    border: none;
}}

QFrame#thicknessLine {{
    background-color: {text};
    border-radius: 2px;
}}

QPushButton#scaleStepButton {{
    background-color: {bg_inner};
    border: 1px solid {border};
    border-radius: 10px;
    color: {text};
    font-size: {font_button_big}px;
    font-weight: 600;
    padding: 0px;
}}

QPushButton#scaleStepButton:hover {{
    border: 1px solid {accent_hover};
    background-color: {bg_card};
}}

QPushButton#scaleStepButton:pressed {{
    background-color: {border};
}}

QPushButton#scaleStepButton:disabled {{
    background-color: {bg_inner};
    color: {text_muted};
    border: 1px solid {border};
}}

QComboBox#scaleCombo {{
    background-color: {bg_inner};
    border: 1px solid {border};
    border-radius: 10px;
    color: {text};
    font-size: {font_section}px;
    font-weight: 600;
    padding: 0 {button_padding_x}px;
    min-width: {combo_min_width}px;
}}

QComboBox#scaleCombo:hover {{
    border: 1px solid {accent_hover};
}}

QComboBox#scaleCombo:focus {{
    border: 1px solid {accent};
}}

QComboBox#scaleCombo::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: {combo_drop_width}px;
    border: none;
    background: transparent;
}}

QComboBox#scaleCombo::down-arrow {{
    width: 10px;
    height: 10px;
}}

QComboBox QAbstractItemView {{
    background-color: {bg_inner};
    color: {text};
    border: 1px solid {border};
    outline: none;
    selection-background-color: {accent};
    selection-color: white;
}}

QComboBox#videoCombo {{
    background-color: {bg_inner};
    border: 1px solid {border};
    border-radius: 10px;
    color: {text};
    padding: {input_padding_y}px {input_padding_x}px;
    font-weight: 600;
}}

QComboBox#videoCombo:hover {{
    border: 1px solid {accent_hover};
}}

QComboBox#videoCombo:focus {{
    border: 1px solid {accent};
}}

QComboBox#videoCombo::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: {combo_drop_width}px;
    border: none;
    background: transparent;
}}

QComboBox#videoCombo QAbstractItemView {{
    background-color: {bg_inner};
    color: {text};
    border: 1px solid {border};
    outline: none;
    selection-background-color: {accent};
    selection-color: white;
}}

"""


SESSION_HISTORY_STYLE = """
QWidget#historyPageRoot {{
    background-color: {bg_main};
}}

QWidget#historyPageRoot QLabel {{
    color: {text};
    background: transparent;
}}

QFrame#historySessionsPanel,
QFrame#historyStatsPanel,
QFrame#historyBottomPanel {{
    background-color: {bg_card};
    border: 1px solid {border};
    border-radius: 12px;
}}

QFrame#historyViewerPanel {{
    background-color: {bg_main};
}}

QLabel#panelTitle,
QLabel#historySessionTitle {{
    color: {title};
    font-size: {font_section}px;
    font-weight: 700;
}}

QLabel#mutedLabel {{
    color: {text_muted};
    font-size: {font_caption}px;
}}

QLabel#historyImageViewer {{
    background-color: {bg_card};
    border: 1px solid {border};
    border-radius: 14px;
    color: {text_muted};
    font-size: {font_large}px;
}}

QLineEdit {{
    background-color: {bg_inner};
    border: 1px solid {border};
    border-radius: 10px;
    padding: {input_padding_y}px {input_padding_x}px;
    color: {text};
}}

QLineEdit:hover {{
    border: 1px solid #3A404A;
}}

QLineEdit:focus {{
    border: 1px solid {accent};
}}

QListWidget {{
    background-color: {bg_inner};
    border: 1px solid {border};
    border-radius: 12px;
    padding: 6px;
    outline: none;
}}

QListWidget::item {{
    color: {text};
    padding: {input_padding_y}px {input_padding_x}px;
    border-radius: 8px;
}}

QListWidget::item:hover {{
    background-color: {border};
}}

QListWidget::item:selected {{
    background-color: {accent};
    color: white;
}}

QTabBar {{
    background: transparent;
    border: none;
    outline: none;
}}

QTabBar::base {{
    background: transparent;
    border: none;
    height: 0px;
}}

QTabBar::tab {{
    background-color: {bg_inner};
    color: {text};
    border: 1px solid {border};
    border-radius: 10px;
    padding: {tab_padding_y}px {tab_padding_x}px;
    margin-right: 8px;
    font-weight: 600;
}}

QTabBar::tab:hover {{
    background-color: {border};
}}

QTabBar::tab:selected {{
    background-color: {accent};
    border: 1px solid {accent};
    color: white;
}}

QPushButton {{
    background-color: {accent};
    color: white;
    border: none;
    border-radius: 10px;
    padding: {button_padding_y}px {button_padding_x}px;
    font-weight: 600;
}}

QPushButton:hover {{
    background-color: {accent_hover};
}}

QPushButton:pressed {{
    background-color: {accent_pressed};
}}

QPushButton:disabled {{
    background-color: #3A404A;
    color: #9199A6;
}}

QPushButton#navArrowButton {{
    padding: 0px;
}}

QPushButton#thumbnailButton {{
    background-color: {bg_inner};
    border: 1px solid {border};
    border-radius: 10px;
    padding: 4px;
}}

QPushButton#thumbnailButton:hover {{
    border: 1px solid {accent_hover};
    background-color: {bg_inner};
}}

QPushButton#thumbnailButton:checked {{
    border: 2px solid {accent};
    background-color: {bg_inner};
}}

QTableWidget#statsTable {{
    background-color: {bg_inner};
    border: 1px solid {border};
    border-radius: 12px;
    gridline-color: transparent;
    outline: none;
    padding: 6px;
}}

QTableWidget#statsTable::item {{
    padding: 8px;
    border-radius: 6px;
}}

QTableWidget#statsTable::item:alternate {{
    background-color: {bg_card};
}}

QHeaderView::section {{
    background-color: {bg_card};
    color: {text_muted};
    border: none;
    border-bottom: 1px solid {border};
    padding: 9px;
    font-weight: 600;
}}

QTableCornerButton::section {{
    background-color: {bg_card};
    border: none;
}}

QLabel#statsTotalLabel {{
    color: {title};
    font-size: {font_medium}px;
    font-weight: 600;
}}

QScrollArea {{
    border: none;
    background: transparent;
}}

QScrollArea QWidget {{
    background: transparent;
}}

QScrollBar:vertical,
QScrollBar:horizontal {{
    background: transparent;
    width: {scrollbar_size}px;
    height: {scrollbar_size}px;
}}

QScrollBar::handle:vertical,
QScrollBar::handle:horizontal {{
    background: #3A4655;
    border-radius: 4px;
    min-height: {scrollbar_min_handle}px;
}}

QScrollBar::handle:vertical:hover,
QScrollBar::handle:horizontal:hover {{
    background: #4A5A6D;
}}

QScrollBar::add-line,
QScrollBar::sub-line {{
    width: 0px;
    height: 0px;
    background: transparent;
}}

QScrollBar::add-page,
QScrollBar::sub-page {{
    background: transparent;
}}

QWidget#imageFullscreenOverlay {{
    background-color: rgba(10, 14, 18, 180);
}}

QLabel#fullscreenImageLabel {{
    background-color: transparent;
    border: none;
}}

QMenu {{
    background-color: {bg_inner};
    color: {text};
    border: 1px solid {border};
    border-radius: 10px;
    padding: 6px;
}}

QMenu::item {{
    padding: 8px 28px 8px 14px;
    border-radius: 7px;
}}

QMenu::item:selected {{
    background-color: {accent};
    color: white;
}}

"""
