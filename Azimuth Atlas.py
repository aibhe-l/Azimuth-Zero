import dash

from dash import html

import matplotlib.pyplot as plt

app = dash.Dash(__name__)

import dash
from dash import dcc, html, Input, Output, State

app = dash.Dash(__name__)
app.title = "Azimuth Atlas"

# =====================================================================
# MODIFIABLE TELEMETRY & INPUT VARIABLES
# =====================================================================
uv_level = 9.0          # Set above 8.0 to trigger the solar radiation warning
MAX_UV = 12.0           # Top of the UV scale
UV_BAR_HEIGHT = 140     # Height (in px) of assets/uv.jpeg

wind_speed = 26         # Set above 25 to trigger the dust storm warning
wind_direction = 45     # Angle in degrees (0 = N, 90 = E, 180 = S, 270 = W)

# Updated automatically when the user clicks the "Confirm" button
astro_latitude = None
astro_longitude = None
search_radius = None


def get_uv_marker_top(value, max_val=MAX_UV, bar_height=UV_BAR_HEIGHT):
    """Maps a UV value (0..max_val) to a vertical 'top' offset (in px) along the UV bar."""
    if value is None:
        clamped = 0.0
    else:
        clamped = max(0.0, min(float(value), float(max_val)))
    ratio = clamped / float(max_val) if max_val else 0.0
    usable_height = bar_height - 8
    return round(4 + (1.0 - ratio) * usable_height, 1)


# Reusable style for transparent clickable button overlays
TRANSPARENT_BTN_OVERLAY_STYLE = {
    'position': 'absolute',
    'top': '0',
    'left': '0',
    'width': '100%',
    'height': '100%',
    'backgroundColor': 'transparent',
    'border': 'none',
    'borderRadius': '8px',
    'padding': '0',
    'margin': '0',
    'cursor': 'pointer',
    'zIndex': '20'
}


app.layout = html.Div([

    # Stores for syncing variables with callbacks
    dcc.Store(id='confirmed-inputs-store', data={
        'latitude': astro_latitude,
        'longitude': astro_longitude,
        'radius': search_radius
    }),
    dcc.Store(id='wind-speed-store', data=wind_speed),
    dcc.Store(id='wind-direction-store', data=wind_direction),
    dcc.Store(id='uv-level-store', data=uv_level),

    # --- HEADER ---
    html.Div([

        # Left Group: Logo and team name
        html.Div([
            html.Img(src='assets/azimuth-logo.png', style={'height': '50px', 'marginRight': '15px'}),
            html.H1('Azimuth Zero', style={
                'margin': '0',
                'fontSize': '20px',
                'color': 'white',
                'whiteSpace': 'nowrap'
            }),
        ], style={'display': 'flex', 'alignItems': 'center'}),

        # Middle Group: App title and outline
        html.Div([
            html.H1('Azimuth Atlas', style={
                'margin': '0',
                'fontSize': '20px',
                'color': 'white',
                'fontWeight': 'bold',
                'whiteSpace': 'nowrap'
            }),

            # Geometric parallelogram underline
            html.Div([
                html.Div(style={'backgroundColor': '#004d89', 'height': '6px', 'width': '50%', 'transform': 'skewX(-45deg)'}),
                html.Div(style={'backgroundColor': '#cda961', 'height': '6px', 'width': '50%', 'transform': 'skewX(-45deg)'})
            ], style={
                'display': 'flex',
                'marginTop': '5px',
                'marginLeft': '4px'
            })

        ], style={
            'position': 'absolute',
            'left': '43%',
            'transform': 'translateX(-50%)',
            'marginTop': '11px'
        }),

        # Right Group: Dynamic Warning Rounded Rectangle
        html.Div(
            id='warning-banner',
            style={
                'display': 'flex',
                'alignItems': 'center',
                'backgroundColor': '#004d89',
                'borderRadius': '10px',
                'padding': '10px 16px',
                'marginLeft': 'auto'
            }
        )

    ], style={
        'display': 'flex',
        'alignItems': 'center',
        'padding': '15px',
        'position': 'relative',
        'zIndex': '10'
    }),

    # --- UPPER LEFT: COORDINATES & RADIUS BOX ---
    html.Div([

        # Latitude & Longitude Row
        html.Div([
            dcc.Input(
                id='astro-lat-input',
                type='number',
                placeholder='Latitude',
                style={
                    'flex': '1',
                    'minWidth': '0',
                    'marginRight': '6px',
                    'boxSizing': 'border-box',
                    'backgroundColor': '#161621',
                    'color': '#ffffff',
                    'border': '1px solid #4a90c2',
                    'borderRadius': '6px',
                    'padding': '6px 4px',
                    'fontSize': '12px',
                    'textAlign': 'left'
                }
            ),
            dcc.Input(
                id='astro-lon-input',
                type='number',
                placeholder='Longitude',
                style={
                    'flex': '1',
                    'minWidth': '0',
                    'boxSizing': 'border-box',
                    'backgroundColor': '#161621',
                    'color': '#ffffff',
                    'border': '1px solid #4a90c2',
                    'borderRadius': '6px',
                    'padding': '6px 4px',
                    'fontSize': '12px',
                    'textAlign': 'left'
                }
            )
        ], style={'display': 'flex', 'marginBottom': '8px'}),

        # Manual Radius (km) Input + Confirm Button
        html.Div([
            dcc.Input(
                id='search-radius-input',
                type='text',
                placeholder='Radius (km)',
                style={
                    'flex': '1',
                    'minWidth': '0',
                    'marginRight': '6px',
                    'boxSizing': 'border-box',
                    'backgroundColor': '#161621',
                    'color': '#ffffff',
                    'border': '1px solid #4a90c2',
                    'borderRadius': '6px',
                    'padding': '6px 4px',
                    'fontSize': '12px',
                    'textAlign': 'left'
                }
            ),
            html.Button(
                "Confirm",
                id='search-locations-btn',
                n_clicks=0,
                style={
                    'backgroundColor': '#cda961',
                    'color': '#161621',
                    'border': 'none',
                    'borderRadius': '6px',
                    'padding': '6px 10px',
                    'fontSize': '12px',
                    'fontWeight': 'bold',
                    'cursor': 'pointer',
                    'whiteSpace': 'nowrap'
                }
            )
        ], style={'display': 'flex', 'marginBottom': '8px'}),

        # Open/Blank Space for Future Location Options
        html.Div(
            id='location-options-area',
            children=[
                dcc.RadioItems(
                    id='location-options-radio',
                    options=[],
                    style={
                        'fontSize': '12px',
                        'color': '#ffffff',
                        'display': 'flex',
                        'flexDirection': 'column',
                        'gap': '4px'
                    }
                )
            ],
            style={
                'flex': '1',
                'minHeight': '28px',
                'overflowY': 'auto',
                'backgroundColor': '#161621',
                'borderRadius': '8px',
                'padding': '8px',
                'boxSizing': 'border-box'
            }
        )

    ], style={
        'position': 'fixed',
        'top': '84px',
        'height': '188px',
        'left': '20px',
        'width': '235px',
        'backgroundColor': '#004d89',
        'borderRadius': '12px',
        'padding': '12px',
        'boxSizing': 'border-box',
        'display': 'flex',
        'flexDirection': 'column',
        'zIndex': '10'
    }),

    # --- CENTRE BOX (Map Area) ---
    html.Div([
        html.Div(
            id='top-center-box',
            style={
                'flex': '1',
                'width': '100%',
                'backgroundColor': '#004d89',
                'borderRadius': '12px',
                'padding': '16px',
                'boxSizing': 'border-box',
                'overflow': 'hidden'
            }
        )
    ], style={
        'position': 'fixed',
        'top': '84px',
        'bottom': '20px',
        'left': '275px',
        'right': '85px',
        'display': 'flex',
        'flexDirection': 'column',
        'zIndex': '5'
    }),

    # --- WIND WHEEL + ROTATABLE ARROW ---
    html.Div([
        # Background Wheel
        html.Img(src='assets/cardinal-wheel.png', style={
            'height': '146px',
            'width': '120px',
            'display': 'block'
        }),

        # Superimposed Center Arrow (Rotates around its center)
        html.Img(
            id='compass-direction-arrow',
            src='assets/direction-arrow.png',
            style={
                'position': 'absolute',
                'top': '56%',
                'left': '50%',
                'transform': 'translate(-50%, -50%) rotate(0deg)',
                'transformOrigin': 'center center',
                'height': '104px',
                'width': 'auto',
                'transition': 'transform 0.2s ease'
            }
        )
    ], style={
        'position': 'fixed',
        'bottom': '66px',
        'left': '160px',
        'transform': 'translateX(-50%)',
        'zIndex': '10'
    }),

    # --- BOTTOM LEFT: ZOOM ICONS + VARIABLE WIND SPEED BOX ---
    html.Div([

        # Zoom Icons with Transparent Clickable Overlays
        html.Div([
            html.Div([
                html.Img(src='assets/zoom-in.svg', style={
                    'height': '25px',
                    'width': '25px',
                    'display': 'block',
                    'filter': 'brightness(0) invert(1)'
                }),
                html.Button(
                    id='zoom-in-btn',
                    n_clicks=0,
                    title='Zoom In',
                    style=TRANSPARENT_BTN_OVERLAY_STYLE
                )
            ], style={
                'position': 'relative',
                'backgroundColor': '#004d89',
                'borderRadius': '8px',
                'padding': '8px',
                'marginBottom': '10px'
            }),

            html.Div([
                html.Img(src='assets/zoom-out.svg', style={
                    'height': '25px',
                    'width': '25px',
                    'display': 'block',
                    'filter': 'brightness(0) invert(1)'
                }),
                html.Button(
                    id='zoom-out-btn',
                    n_clicks=0,
                    title='Zoom Out',
                    style=TRANSPARENT_BTN_OVERLAY_STYLE
                )
            ], style={
                'position': 'relative',
                'backgroundColor': '#004d89',
                'borderRadius': '8px',
                'padding': '8px'
            })
        ], style={
            'display': 'flex',
            'flexDirection': 'column'
        }),

        # Wind Speed Box
        html.Div([
            html.Span(
                '',
                id='wind-speed-text',
                style={
                    'color': 'white',
                    'fontSize': '14px',
                    'fontWeight': 'bold',
                    'whiteSpace': 'nowrap'
                }
            )
        ], style={
            'backgroundColor': '#004d89',
            'borderRadius': '10px',
            'padding': '10px 16px',
            'marginLeft': '22px',
            'marginRight': '22px',
            'textAlign': 'center'
        })

    ], style={
        'position': 'fixed',
        'bottom': '20px',
        'left': '20px',
        'display': 'flex',
        'alignItems': 'flex-end',
        'zIndex': '10'
    }),

    # --- RIGHT SIDE: TWO ICON BOXES + UV LABEL + UV BAR + MARKER ---
    html.Div([

        # Satellite Box + Transparent Button Overlay
        html.Div([
            html.Img(src='assets/satellite.svg', style={
                'height': '25px',
                'width': '25px',
                'display': 'block',
                'filter': 'brightness(0) invert(1)'
            }),
            html.Button(
                id='satellite-btn',
                n_clicks=0,
                title='Satellite View',
                style=TRANSPARENT_BTN_OVERLAY_STYLE
            )
        ], style={
            'position': 'relative',
            'backgroundColor': '#004d89',
            'borderRadius': '8px',
            'padding': '8px',
            'marginBottom': '10px'
        }),

        # Mountain Box + Transparent Button Overlay
        html.Div([
            html.Img(src='assets/mountain.png', style={
                'height': '25px',
                'width': '25px',
                'display': 'block',
                'filter': 'brightness(0) invert(1)'
            }),
            html.Button(
                id='mountain-btn',
                n_clicks=0,
                title='Terrain / Elevation View',
                style=TRANSPARENT_BTN_OVERLAY_STYLE
            )
        ], style={
            'position': 'relative',
            'backgroundColor': '#004d89',
            'borderRadius': '8px',
            'padding': '8px',
            'marginBottom': '12px'
        }),

        # UV Label + UV Radiation Colour Bar + Marker
        html.Div([
            html.Div([
                html.Span('UV', style={
                    'color': 'white',
                    'fontSize': '14px',
                    'fontWeight': 'bold',
                    'whiteSpace': 'nowrap'
                })
            ], style={
                'backgroundColor': '#004d89',
                'borderRadius': '8px',
                'padding': '5px 12px',
                'marginBottom': '6px',
                'textAlign': 'center'
            }),

            html.Div([
                html.Img(src='assets/uv.jpeg', style={
                    'height': f'{UV_BAR_HEIGHT}px',
                    'width': '22px',
                    'display': 'block',
                    'borderRadius': '6px'
                }),
                html.Div(
                    id='uv-level-marker',
                    style={
                        'position': 'absolute',
                        'left': '-5px',
                        'width': '32px',
                        'top': '0px',
                        'transform': 'translateY(-50%)',
                        'height': '8px',
                        'backgroundColor': '#cda961',
                        'borderRadius': '999px',
                        'boxShadow': '0 1px 3px rgba(0, 0, 0, 0.45)',
                        'pointerEvents': 'none',
                        'zIndex': '25',
                        'transition': 'top 0.15s ease'
                    }
                )
            ], style={
                'position': 'relative',
                'height': f'{UV_BAR_HEIGHT}px',
                'width': '22px',
                'overflow': 'visible'
            })
        ], style={
            'display': 'flex',
            'flexDirection': 'column',
            'alignItems': 'center'
        })

    ], style={
        'position': 'fixed',
        'bottom': '20px',
        'right': '20px',
        'display': 'flex',
        'flexDirection': 'column',
        'alignItems': 'center',
        'zIndex': '10'
    })

], style={
    'backgroundColor': '#161621',
    'minHeight': '100vh',
    'color': '#ffffff',
    'position': 'relative'
})


# =====================================================================
# CALLBACKS
# =====================================================================

@app.callback(
    Output('confirmed-inputs-store', 'data'),
    Input('search-locations-btn', 'n_clicks'),
    State('astro-lat-input', 'value'),
    State('astro-lon-input', 'value'),
    State('search-radius-input', 'value'),
    prevent_initial_call=True
)
def save_confirmed_search_inputs(n_clicks, lat_val, lon_val, radius_val):
    global astro_latitude, astro_longitude, search_radius

    astro_latitude = float(lat_val) if lat_val is not None and str(lat_val).strip() != '' else None
    astro_longitude = float(lon_val) if lon_val is not None and str(lon_val).strip() != '' else None

    try:
        search_radius = float(radius_val) if radius_val is not None and str(radius_val).strip() != '' else None
    except ValueError:
        search_radius = None

    return {
        'latitude': astro_latitude,
        'longitude': astro_longitude,
        'radius': search_radius
    }


@app.callback(
    Output('wind-speed-text', 'children'),
    Input('wind-speed-store', 'data')
)
def update_wind_speed(wind):
    return f'Wind Speed: {wind} m/s'


@app.callback(
    Output('compass-direction-arrow', 'style'),
    Input('wind-direction-store', 'data')
)
def update_compass(direction):
    return {
        'position': 'absolute',
        'top': '56%',
        'left': '50%',
        'transform': f'translate(-50%, -50%) rotate({direction}deg)',
        'transformOrigin': 'center center',
        'height': '104px',
        'width': 'auto',
        'transition': 'transform 0.2s ease'
    }


@app.callback(
    Output('uv-level-marker', 'style'),
    Input('uv-level-store', 'data')
)
def update_uv_marker(current_uv):
    top_px = get_uv_marker_top(current_uv)
    return {
        'position': 'absolute',
        'left': '-5px',
        'width': '32px',
        'top': f'{top_px}px',
        'transform': 'translateY(-50%)',
        'height': '8px',
        'backgroundColor': "#ffffff",
        'borderRadius': '999px',
        'boxShadow': '0 1px 3px rgba(0, 0, 0, 0.45)',
        'pointerEvents': 'none',
        'zIndex': '25',
        'transition': 'top 0.15s ease'
    }


@app.callback(
    Output('warning-banner', 'children'),
    Input('wind-speed-store', 'data'),
    Input('uv-level-store', 'data')
)
def update_warning_banner(wind, uv):
    
    if wind >= 25.0 and uv >= 8.0:
        return [
            html.Img(src='assets/exclamation-triangle.svg', style={'height': '24px', 'width': '24px', 'marginRight': '12px', 'filter': 'brightness(0) invert(1)'}),
            html.Span('Risk of dust storm and excessive radiation.', style={'color': 'white', 'fontSize': '14px', 'fontWeight': 'bold', 'whiteSpace': 'nowrap'})
        ]
    
    elif wind >= 25.0:
        return [
            html.Img(src='assets/exclamation-triangle.svg', style={'height': '24px', 'width': '24px', 'marginRight': '12px', 'filter': 'brightness(0) invert(1)'}),
            html.Span('Risk of dust storm.', style={'color': 'white', 'fontSize': '14px', 'fontWeight': 'bold', 'whiteSpace': 'nowrap'})
        ]
    elif uv >= 8.0:
        return [
            html.Img(src='assets/exclamation-triangle.svg', style={'height': '24px', 'width': '24px', 'marginRight': '12px', 'filter': 'brightness(0) invert(1)'}),
            html.Span('Dangerously elevated solar radiation.', style={'color': 'white', 'fontSize': '14px', 'fontWeight': 'bold', 'whiteSpace': 'nowrap'})
        ]
    else:
        return [
            html.Img(src='assets/check-circle.svg', style={'height': '24px', 'width': '24px', 'marginRight': '12px', 'filter': 'brightness(0) invert(1)'}),
            html.Span('No extreme weather events detected.', style={'color': 'white', 'fontSize': '14px', 'fontWeight': 'bold', 'whiteSpace': 'nowrap'})
        ]


if __name__ == '__main__':
    app.run(debug=True)