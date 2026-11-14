import dash

from dash import html

import matplotlib.pyplot as plt

app = dash.Dash(__name__)

import dash
from dash import html
from dash import dcc

app = dash.Dash(__name__)
app.title = "Azimuth Atlas"

app.layout = html.Div([

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

        # Right Group: Warning Rounded Rectangle
        html.Div([
            html.Img(src='assets/exclamation-triangle.svg', style={
                'height': '24px',
                'width': '24px',
                'marginRight': '12px',
                'filter': 'brightness(0) invert(1)'
            }),
            html.Span('Excessive radiation: seek shelter and avoid EVAs', style={
                'color': 'white',
                'fontSize': '14px',
                'fontWeight': 'bold',
                'whiteSpace': 'nowrap'
            })
        ], style={
            'display': 'flex',
            'alignItems': 'center',
            'backgroundColor': '#004d89',
            'borderRadius': '10px',
            'padding': '10px 16px',
            'marginLeft': 'auto'
        })

    ], style={
        'display': 'flex',
        'alignItems': 'center',
        'padding': '15px',
        'position': 'relative',
        'zIndex': '10'
    }),

    # --- UPPER LEFT: ASTRONAUT COORDINATES, RADIUS & LOCATION SELECTOR ---
    html.Div([
        html.Div(
            "Astronaut Coordinates & Search",
            style={
                'fontSize': '14px',
                'fontWeight': 'bold',
                'color': '#ffffff',
                'marginBottom': '10px'
            }
        ),

        # Latitude & Longitude Row
        html.Div([
            html.Div([
                html.Label("Lat", style={'fontSize': '11px', 'color': '#d0d7de', 'display': 'block', 'marginBottom': '3px'}),
                dcc.Input(
                    id='astro-lat-input',
                    type='number',
                    placeholder='Lat',
                    style={
                        'width': '100%',
                        'boxSizing': 'border-box',
                        'backgroundColor': '#161621',
                        'color': '#ffffff',
                        'border': '1px solid #4a90c2',
                        'borderRadius': '6px',
                        'padding': '5px 7px',
                        'fontSize': '12px'
                    }
                )
            ], style={'flex': '1', 'marginRight': '6px'}),

            html.Div([
                html.Label("Lon", style={'fontSize': '11px', 'color': '#d0d7de', 'display': 'block', 'marginBottom': '3px'}),
                dcc.Input(
                    id='astro-lon-input',
                    type='number',
                    placeholder='Lon',
                    style={
                        'width': '100%',
                        'boxSizing': 'border-box',
                        'backgroundColor': '#161621',
                        'color': '#ffffff',
                        'border': '1px solid #4a90c2',
                        'borderRadius': '6px',
                        'padding': '5px 7px',
                        'fontSize': '12px'
                    }
                )
            ], style={'flex': '1'})
        ], style={'display': 'flex', 'marginBottom': '8px'}),

        # Search Radius Input + Search Button
        html.Div([
            html.Div([
                html.Label("Search Radius (km)", style={'fontSize': '11px', 'color': '#d0d7de', 'display': 'block', 'marginBottom': '3px'}),
                dcc.Input(
                    id='search-radius-input',
                    type='number',
                    placeholder='Radius',
                    min=0,
                    style={
                        'width': '100%',
                        'boxSizing': 'border-box',
                        'backgroundColor': '#161621',
                        'color': '#ffffff',
                        'border': '1px solid #4a90c2',
                        'borderRadius': '6px',
                        'padding': '5px 7px',
                        'fontSize': '12px'
                    }
                )
            ], style={'flex': '1', 'marginRight': '6px'}),

            html.Button(
                "Find",
                id='search-locations-btn',
                n_clicks=0,
                style={
                    'backgroundColor': '#161621',
                    'color': '#ffffff',
                    'border': '1px solid #cda961',
                    'borderRadius': '6px',
                    'padding': '6px 10px',
                    'fontSize': '12px',
                    'fontWeight': 'bold',
                    'cursor': 'pointer',
                    'alignSelf': 'flex-end'
                }
            )
        ], style={'display': 'flex', 'marginBottom': '10px'}),

        # Blank Space Where Candidate Locations Appear
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
                'minHeight': '78px',
                'maxHeight': '110px',
                'overflowY': 'auto',
                'backgroundColor': '#161621',
                'borderRadius': '8px',
                'padding': '8px',
                'marginBottom': '10px',
                'boxSizing': 'border-box'
            }
        ),

        # Confirm Destination Button
        html.Button(
            "Confirm Destination",
            id='confirm-destination-btn',
            n_clicks=0,
            style={
                'width': '100%',
                'backgroundColor': '#cda961',
                'color': '#161621',
                'border': 'none',
                'borderRadius': '6px',
                'padding': '7px 10px',
                'fontSize': '12px',
                'fontWeight': 'bold',
                'cursor': 'pointer'
            }
        )

    ], style={
        'position': 'fixed',
        'top': '88px',
        'left': '20px',
        'width': '235px',
        'backgroundColor': '#004d89',
        'borderRadius': '12px',
        'padding': '12px',
        'boxSizing': 'border-box',
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
        'top': '88px',
        'bottom': '20px',
        'left': '275px',
        'right': '85px',
        'display': 'flex',
        'flexDirection': 'column',
        'zIndex': '5'
    }),

    # --- WIND WHEEL + ARROW (Directly Above Wind Speed Box) ---
    html.Div([
        # Background Wheel
        html.Img(src='assets/cardinal-wheel.png', style={
            'height': '180px',
            'width': '145px',
            'display': 'block'
        }),

        # Superimposed Center Arrow
        html.Img(src='assets/direction-arrow.png', style={
            'position': 'absolute',
            'top': '56%',
            'left': '50%',
            'transform': 'translate(-50%, -50%)',
            'height': '128px',
            'width': 'auto'
        })
    ], style={
        'position': 'fixed',
        'bottom': '72px',     # Sits directly above the Wind Speed box
        'left': '118px',      # Aligned horizontally over the Wind Speed box
        'zIndex': '10'
    }),

    # --- BOTTOM LEFT: ZOOM ICONS + WIND SPEED BOX ---
    html.Div([

        # Zoom Icons
        html.Div([
            html.Div([
                html.Img(src='assets/zoom-in.svg', style={
                    'height': '25px',
                    'width': '25px',
                    'display': 'block',
                    'filter': 'brightness(0) invert(1)'
                })
            ], style={
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
                })
            ], style={
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
            html.Span('Wind Speed: 14 m/s', style={
                'color': 'white',
                'fontSize': '14px',
                'fontWeight': 'bold',
                'whiteSpace': 'nowrap'
            })
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

    # --- RIGHT SIDE: ICON BOX + UV LABEL + UV RADIATION COLOUR BAR ---
    html.Div([

        # Top Blue Rounded Square Box
        html.Div([
            html.Img(src='assets/mountain.png', style={
                'height': '25px',
                'width': '25px',
                'display': 'block',
                'filter': 'brightness(0) invert(1)'
            })
        ], style={
            'backgroundColor': '#004d89',
            'borderRadius': '8px',
            'padding': '8px',
            'marginBottom': '12px'
        }),

        # UV Label + UV Radiation Colour Bar
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

            html.Img(src='assets/uv.jpeg', style={
                'height': '140px',
                'width': '22px',
                'display': 'block',
                'borderRadius': '6px'
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

if __name__ == '__main__':
    app.run(debug=True)