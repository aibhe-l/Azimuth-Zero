import dash
from dash import dcc, html, Input, Output, State, ALL, ctx
from route import search_area, find_route

app = dash.Dash(__name__)
app.title = "Azimuth Atlas"

# Hardcoded parameters and colour palette

GOLD_HEX = "#cda961"
BLUE_HEX = "#004d89"
DARK_BG = "#161621"

uv_level = 8.0          # Hardcoded UV level (0.0 to 10.0; >= 8.0 triggers warning)
MAX_UV = 10.0
UV_BAR_HEIGHT = 120

wind_speed = 42.0       # Hardcoded Wind Speed in m/s (>= 25.0 triggers warning)
wind_direction = 290.0   # Hardcoded Wind Direction in degrees (0 = N, 90 = E, 180 = S, 270 = W)

# Updated automatically when the user clicks the "Confirm" button
astro_latitude = None
astro_longitude = None
search_radius = None


def get_uv_marker_top(value, max_val=MAX_UV, bar_height=UV_BAR_HEIGHT):
    """Maps a UV value (0..max_val) to a vertical max pixel position along the UV bar."""
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
    'outline': 'none',
    'boxShadow': 'none',
    'borderRadius': '8px',
    'padding': '0',
    'margin': '0',
    'cursor': 'pointer',
    'zIndex': '20'
}


app.layout = html.Div([

    # State stores
    dcc.Store(id='confirmed-inputs-store', data={
        'latitude': astro_latitude,
        'longitude': astro_longitude,
        'radius': search_radius
    }),
    dcc.Store(id='aerial-mode-store', data=True),          # True = Satellite (default), False = Topographical
    dcc.Store(id='view-mode-store', data='mars'),          
    dcc.Store(id='selected-target-store', data=None),      
    dcc.Store(id='wind-speed-store', data=wind_speed),
    dcc.Store(id='wind-direction-store', data=wind_direction),
    dcc.Store(id='uv-level-store', data=uv_level),

    # Header Bar with Logo, Centered App Title, and Dynamic Warning Banner
    html.Div([

        # Left Group: Logo and team name
        html.Div([
            html.Img(src='assets/azimuth-logo.png', style={'height': '42px', 'marginRight': '12px'}),
            html.H1('Azimuth Zero', style={
                'margin': '0',
                'fontSize': '18px',
                'color': 'white',
                'whiteSpace': 'nowrap'
            }),
        ], style={'display': 'flex', 'alignItems': 'center'}),

        # Middle Group: Centered App title and #004d89 / #cda961 geometric underline
        html.Div([
            html.H1('Azimuth Atlas', style={
                'margin': '0',
                'fontSize': '18px',
                'color': 'white',
                'fontWeight': 'bold',
                'whiteSpace': 'nowrap',
                'textAlign': 'center'
            }),
            html.Div([
                html.Div(style={'backgroundColor': BLUE_HEX, 'height': '5px', 'width': '50%', 'transform': 'skewX(-45deg)'}),
                html.Div(style={'backgroundColor': GOLD_HEX, 'height': '5px', 'width': '50%', 'transform': 'skewX(-45deg)'})
            ], style={
                'display': 'flex',
                'marginTop': '4px'
            })

        ], style={
            'position': 'absolute',
            'left': '50%',
            'top': '50%',
            'transform': 'translate(-50%, -50%)'
        }),

        # Right Group: Dynamic Warning Rounded Rectangle
        html.Div(
            id='warning-banner',
            style={
                'display': 'flex',
                'alignItems': 'center',
                'backgroundColor': BLUE_HEX,
                'borderRadius': '10px',
                'padding': '8px 14px',
                'marginLeft': 'auto'
            }
        )

    ], style={
        'display': 'flex',
        'alignItems': 'center',
        'padding': '12px 16px',
        'position': 'relative',
        'zIndex': '10'
    }),

    # Upper Left Box: Latitude, Longitude, Radius Inputs + Confirm Button + Scrollable 2-Column List
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
                    'backgroundColor': DARK_BG,
                    'color': '#ffffff',
                    'border': '1px solid #4a90c2',
                    'borderRadius': '6px',
                    'padding': '5px 4px',
                    'fontSize': '11px',
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
                    'backgroundColor': DARK_BG,
                    'color': '#ffffff',
                    'border': '1px solid #4a90c2',
                    'borderRadius': '6px',
                    'padding': '5px 4px',
                    'fontSize': '11px',
                    'textAlign': 'left'
                }
            )
        ], style={'display': 'flex', 'marginBottom': '6px'}),

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
                    'backgroundColor': DARK_BG,
                    'color': '#ffffff',
                    'border': '1px solid #4a90c2',
                    'borderRadius': '6px',
                    'padding': '5px 4px',
                    'fontSize': '11px',
                    'textAlign': 'left'
                }
            ),
            html.Button(
                "Confirm",
                id='search-locations-btn',
                n_clicks=0,
                style={
                    'backgroundColor': GOLD_HEX,
                    'color': DARK_BG,
                    'border': 'none',
                    'borderRadius': '6px',
                    'padding': '5px 10px',
                    'fontSize': '11px',
                    'fontWeight': 'bold',
                    'cursor': 'pointer',
                    'whiteSpace': 'nowrap'
                }
            )
        ], style={'display': 'flex', 'marginBottom': '6px'}),

        # Scrollable 2-Column List of Points of Interest (Name + Distance)
        html.Div(
            id='location-options-area',
            children=[],
            style={
                'flex': '1',
                'minHeight': '28px',
                'overflowY': 'auto',
                'backgroundColor': DARK_BG,
                'borderRadius': '8px',
                'padding': '6px',
                'boxSizing': 'border-box',
                'display': 'flex',
                'flexDirection': 'column',
                'gap': '4px'
            }
        )

    ], style={
        'position': 'absolute',
        'top': '68px',
        'height': '210px',
        'left': '16px',
        'width': '220px',
        'backgroundColor': BLUE_HEX,
        'borderRadius': '12px',
        'padding': '10px',
        'boxSizing': 'border-box',
        'display': 'flex',
        'flexDirection': 'column',
        'zIndex': '10'
    }),

    # Centre Box: Map Display (Starts by presenting mars.jpg, then updates to search area or route SVGs)
    html.Div([
        html.Div(
            id='top-center-box',
            style={
                'flex': '1',
                'width': '100%',
                'height': '100%',
                'backgroundColor': BLUE_HEX,
                'borderRadius': '12px',
                'padding': '6px',
                'boxSizing': 'border-box',
                'overflow': 'hidden',
                'position': 'relative',
                'display': 'flex',
                'alignItems': 'center',
                'justifyContent': 'center'
            },
            children=[
                html.Img(
                    id='central-map-image',
                    src='assets/mars.jpg',
                    style={
                        'width': '100%',
                        'height': '100%',
                        'objectFit': 'cover',
                        'borderRadius': '8px',
                        'display': 'block'
                    }
                )
            ]
        )
    ], style={
        'position': 'absolute',
        'top': '68px',
        'bottom': '16px',
        'left': '252px',
        'right': '74px',
        'display': 'flex',
        'flexDirection': 'column',
        'zIndex': '5'
    }),

    # Wind wheel with superimposed arrow
    html.Div([
        html.Img(src='assets/cardinal-wheel.png', style={
            'height': '146px',
            'width': '120px',
            'display': 'block'
        }),
        html.Img(
            id='compass-direction-arrow',
            src='assets/direction-arrow.png',
            style={
                'position': 'absolute',
                'top': '56%',
                'left': '50%',
                'transform': f'translate(-50%, -50%) rotate({wind_direction}deg)',
                'transformOrigin': 'center center',
                'height': '104px',
                'width': 'auto',
                'transition': 'transform 0.2s ease'
            }
        )
    ], style={
        'position': 'absolute',
        'bottom': '62px',
        'left': '148px',
        'transform': 'translateX(-50%)',
        'zIndex': '10'
    }),

    # Bottom Left Box: Zoom In/Out Buttons + Wind Speed Box
    html.Div([

        # Zoom Icons
        html.Div([
            html.Div([
                html.Img(src='assets/zoom-in.svg', style={
                    'height': '22px',
                    'width': '22px',
                    'display': 'block',
                    'filter': 'brightness(0) invert(1)'
                }),
                html.Button(
                    id='zoom-in-btn',
                    n_clicks=0,
                    title='Zoom In to Route View',
                    style=TRANSPARENT_BTN_OVERLAY_STYLE
                )
            ], style={
                'position': 'relative',
                'backgroundColor': BLUE_HEX,
                'borderRadius': '8px',
                'padding': '7px',
                'marginBottom': '8px'
            }),

            html.Div([
                html.Img(src='assets/zoom-out.svg', style={
                    'height': '22px',
                    'width': '22px',
                    'display': 'block',
                    'filter': 'brightness(0) invert(1)'
                }),
                html.Button(
                    id='zoom-out-btn',
                    n_clicks=0,
                    title='Zoom Out to Search Radius View',
                    style=TRANSPARENT_BTN_OVERLAY_STYLE
                )
            ], style={
                'position': 'relative',
                'backgroundColor': BLUE_HEX,
                'borderRadius': '8px',
                'padding': '7px'
            })
        ], style={
            'display': 'flex',
            'flexDirection': 'column'
        }),

        # Wind Speed Box
        html.Div([
            html.Span(
                f'Wind Speed: {wind_speed:.1f} m/s',
                id='wind-speed-text',
                style={
                    'color': 'white',
                    'fontSize': '13px',
                    'fontWeight': 'bold',
                    'whiteSpace': 'nowrap'
                }
            )
        ], style={
            'backgroundColor': BLUE_HEX,
            'borderRadius': '10px',
            'padding': '9px 14px',
            'marginLeft': '18px',
            'marginRight': '18px',
            'textAlign': 'center'
        })

    ], style={
        'position': 'absolute',
        'bottom': '16px',
        'left': '16px',
        'display': 'flex',
        'alignItems': 'flex-end',
        'zIndex': '10'
    }),

    # Right side vertical stack: Satellite Button, Mountain Button, UV Bar
    html.Div([

        # Satellite Box (Default Active -> #cda961 highlight)
        html.Div(
            id='satellite-box',
            children=[
                html.Img(src='assets/satellite.svg', style={
                    'height': '22px',
                    'width': '22px',
                    'display': 'block',
                    'filter': 'brightness(0) invert(1)'
                }),
                html.Button(
                    id='satellite-btn',
                    n_clicks=0,
                    title='Satellite View (Default)',
                    style=TRANSPARENT_BTN_OVERLAY_STYLE
                )
            ],
            style={
                'position': 'relative',
                'backgroundColor': GOLD_HEX,
                'border': f'2px solid {GOLD_HEX}',
                'borderRadius': '8px',
                'padding': '6px',
                'marginBottom': '8px',
                'boxSizing': 'border-box'
            }
        ),

        # Mountain Box
        html.Div(
            id='mountain-box',
            children=[
                html.Img(src='assets/mountain.png', style={
                    'height': '22px',
                    'width': '22px',
                    'display': 'block',
                    'filter': 'brightness(0) invert(1)'
                }),
                html.Button(
                    id='mountain-btn',
                    n_clicks=0,
                    title='Topographical View',
                    style=TRANSPARENT_BTN_OVERLAY_STYLE
                )
            ],
            style={
                'position': 'relative',
                'backgroundColor': BLUE_HEX,
                'border': f'2px solid {BLUE_HEX}',
                'borderRadius': '8px',
                'padding': '6px',
                'marginBottom': '10px',
                'boxSizing': 'border-box'
            }
        ),

        # UV Label + Bar + #cda961 Marker
        html.Div([
            html.Div([
                html.Span('UV', style={
                    'color': 'white',
                    'fontSize': '13px',
                    'fontWeight': 'bold',
                    'whiteSpace': 'nowrap'
                })
            ], style={
                'backgroundColor': BLUE_HEX,
                'borderRadius': '8px',
                'padding': '4px 10px',
                'marginBottom': '5px',
                'textAlign': 'center'
            }),

            html.Div([
                html.Img(src='assets/uv.jpeg', style={
                    'height': f'{UV_BAR_HEIGHT}px',
                    'width': '20px',
                    'display': 'block',
                    'borderRadius': '6px'
                }),
                html.Div(
                    id='uv-level-marker',
                    style={
                        'position': 'absolute',
                        'left': '-5px',
                        'width': '30px',
                        'top': f'{get_uv_marker_top(uv_level)}px',
                        'transform': 'translateY(-50%)',
                        'height': '8px',
                        'backgroundColor': GOLD_HEX,
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
                'width': '20px',
                'overflow': 'visible'
            })
        ], style={
            'display': 'flex',
            'flexDirection': 'column',
            'alignItems': 'center'
        })

    ], style={
        'position': 'absolute',
        'bottom': '16px',
        'right': '16px',
        'display': 'flex',
        'flexDirection': 'column',
        'alignItems': 'center',
        'zIndex': '10'
    })

], style={
    'backgroundColor': DARK_BG,
    'width': '1024px',
    'height': '580px',
    'margin': '10px auto',
    'position': 'relative',
    'overflow': 'hidden',
    'color': '#ffffff',
    'boxShadow': '0 4px 20px rgba(0,0,0,0.5)',
    'borderRadius': '10px'
})

# Callbacks

# 1. Save latitude, longitude, and radius when Confirm is clicked
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

    try:
        astro_latitude = float(lat_val) if lat_val is not None and str(lat_val).strip() != '' else None
        astro_longitude = float(lon_val) if lon_val is not None and str(lon_val).strip() != '' else None
        search_radius = float(radius_val) if radius_val is not None and str(radius_val).strip() != '' else None
    except ValueError:
        astro_latitude, astro_longitude, search_radius = None, None, None

    return {
        'latitude': astro_latitude,
        'longitude': astro_longitude,
        'radius': search_radius
    }


# Toggle between Satellite (aerial=True) and Topographical (aerial=False)
@app.callback(
    Output('aerial-mode-store', 'data'),
    Output('satellite-box', 'style'),
    Output('mountain-box', 'style'),
    Input('satellite-btn', 'n_clicks'),
    Input('mountain-btn', 'n_clicks'),
    State('aerial-mode-store', 'data'),
    prevent_initial_call=True
)
def toggle_aerial_mode(sat_clicks, mtn_clicks, current_aerial):
    triggered = ctx.triggered_id
    if triggered == 'satellite-btn':
        aerial = True
    elif triggered == 'mountain-btn':
        aerial = False
    else:
        aerial = current_aerial

    sat_style = {
        'position': 'relative',
        'backgroundColor': GOLD_HEX if aerial else BLUE_HEX,
        'border': f'2px solid {GOLD_HEX}' if aerial else f'2px solid {BLUE_HEX}',
        'borderRadius': '8px',
        'padding': '6px',
        'marginBottom': '8px',
        'boxSizing': 'border-box'
    }
    mtn_style = {
        'position': 'relative',
        'backgroundColor': GOLD_HEX if not aerial else BLUE_HEX,
        'border': f'2px solid {GOLD_HEX}' if not aerial else f'2px solid {BLUE_HEX}',
        'borderRadius': '8px',
        'padding': '6px',
        'marginBottom': '10px',
        'boxSizing': 'border-box'
    }
    return aerial, sat_style, mtn_style


# 3. Select a target from the 2-column scrollable list
@app.callback(
    Output('selected-target-store', 'data'),
    Input({'type': 'target-item', 'index': ALL}, 'n_clicks'),
    Input('confirmed-inputs-store', 'data'),
    State('selected-target-store', 'data'),
    prevent_initial_call=True
)
def select_target(target_clicks, confirmed_data, current_selected):
    triggered = ctx.triggered_id
    if triggered == 'confirmed-inputs-store':
        return None
    if isinstance(triggered, dict) and triggered.get('type') == 'target-item':
        if not any(target_clicks):
            return current_selected
        return triggered.get('index')
    return current_selected


# Update the central map and 2-column target list
@app.callback(
    Output('central-map-image', 'src'),
    Output('central-map-image', 'style'),
    Output('location-options-area', 'children'),
    Output('view-mode-store', 'data'),
    Input('confirmed-inputs-store', 'data'),
    Input('selected-target-store', 'data'),
    Input('aerial-mode-store', 'data'),
    Input('zoom-in-btn', 'n_clicks'),
    Input('zoom-out-btn', 'n_clicks'),
    State('view-mode-store', 'data'),
    prevent_initial_call=True
)
def update_map_and_list(confirmed, selected_idx, aerial, zoom_in, zoom_out, current_view):
    lat = confirmed.get('latitude') if confirmed else None
    lon = confirmed.get('longitude') if confirmed else None
    radius = confirmed.get('radius') if confirmed else None

    default_img_style = {
        'width': '100%',
        'height': '100%',
        'objectFit': 'cover',
        'borderRadius': '8px',
        'display': 'block'
    }
    svg_img_style = {
        'maxWidth': '100%',
        'maxHeight': '100%',
        'width': 'auto',
        'height': '100%',
        'objectFit': 'contain',
        'backgroundColor': '#ffffff',
        'borderRadius': '8px',
        'display': 'block'
    }

    if lat is None or lon is None or radius is None or radius <= 0:
        return 'assets/mars.jpg', default_img_style, [], 'mars'

    triggered = ctx.triggered_id

    if triggered == 'confirmed-inputs-store':
        target_view = 'search'
    elif triggered == 'selected-target-store' and selected_idx is not None:
        target_view = 'route'
    elif triggered == 'zoom-out-btn':
        target_view = 'search'
    elif triggered == 'zoom-in-btn' and selected_idx is not None:
        target_view = 'route'
    else:
        target_view = current_view if current_view in ('search', 'route') else 'search'
        if target_view == 'route' and selected_idx is None:
            target_view = 'search'

    svg_uri, targets = search_area(aerial=aerial, lat=lat, lon=lon, radius=radius)

    list_items = []
    for t in targets:
        is_selected = (selected_idx == t['index'])
        list_items.append(
            html.Button(
                id={'type': 'target-item', 'index': t['index']},
                n_clicks=0,
                children=[
                    html.Span(
                        t['name'],
                        style={
                            'textAlign': 'left',
                            'overflow': 'hidden',
                            'textOverflow': 'ellipsis',
                            'whiteSpace': 'nowrap',
                            'marginRight': '8px',
                            'color': '#ffffff'
                        }
                    ),
                    html.Span(
                        f"{t['distance_km']:.2f} km",
                        style={
                            'textAlign': 'right',
                            'color': GOLD_HEX,
                            'fontWeight': 'bold',
                            'whiteSpace': 'nowrap'
                        }
                    )
                ],
                style={
                    'display': 'flex',
                    'justifyContent': 'space-between',
                    'alignItems': 'center',
                    'width': '100%',
                    'backgroundColor': BLUE_HEX if is_selected else '#1e1e2e',
                    'color': '#ffffff',
                    'border': f'1.5px solid {GOLD_HEX}' if is_selected else '1px solid #2e2e42',
                    'outline': 'none',
                    'borderRadius': '5px',
                    'padding': '4px 7px',
                    'fontSize': '11px',
                    'cursor': 'pointer',
                    'boxSizing': 'border-box'
                }
            )
        )

    if not list_items:
        list_items = [
            html.Div(
                "No points of interest in radius.",
                style={'color': '#8b949e', 'fontSize': '11px', 'textAlign': 'center', 'padding': '8px'}
            )
        ]

    if target_view == 'route' and selected_idx is not None:
        try:
            route_svg_uri, target_name, dist_km = find_route(
                selection_index=selected_idx,
                lat=lat,
                lon=lon,
                radius=radius,
                aerial=aerial
            )
            return route_svg_uri, svg_img_style, list_items, 'route'
        except Exception:
            return svg_uri, svg_img_style, list_items, 'search'

    return svg_uri, svg_img_style, list_items, 'search'


# Display hardcoded telemetry values & warning banner on startup
@app.callback(
    Output('wind-speed-text', 'children'),
    Input('wind-speed-store', 'data')
)
def update_wind_speed(wind):
    return f'Wind Speed: {float(wind):.1f} m/s'


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
        'width': '30px',
        'top': f'{top_px}px',
        'transform': 'translateY(-50%)',
        'height': '8px',
        'backgroundColor': GOLD_HEX,
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
            html.Img(src='assets/exclamation-triangle.svg', style={'height': '20px', 'width': '20px', 'marginRight': '10px', 'filter': 'brightness(0) invert(1)'}),
            html.Span('Risk of dust storm and excessive radiation.', style={'color': 'white', 'fontSize': '13px', 'fontWeight': 'bold', 'whiteSpace': 'nowrap'})
        ]
    elif wind >= 25.0:
        return [
            html.Img(src='assets/exclamation-triangle.svg', style={'height': '20px', 'width': '20px', 'marginRight': '10px', 'filter': 'brightness(0) invert(1)'}),
            html.Span('Risk of dust storm.', style={'color': 'white', 'fontSize': '13px', 'fontWeight': 'bold', 'whiteSpace': 'nowrap'})
        ]
    elif uv >= 8.0:
        return [
            html.Img(src='assets/exclamation-triangle.svg', style={'height': '20px', 'width': '20px', 'marginRight': '10px', 'filter': 'brightness(0) invert(1)'}),
            html.Span('Dangerously elevated solar radiation.', style={'color': 'white', 'fontSize': '13px', 'fontWeight': 'bold', 'whiteSpace': 'nowrap'})
        ]
    else:
        return [
            html.Img(src='assets/check-circle.svg', style={'height': '20px', 'width': '20px', 'marginRight': '10px', 'filter': 'brightness(0) invert(1)'}),
            html.Span('No extreme weather events detected.', style={'color': 'white', 'fontSize': '13px', 'fontWeight': 'bold', 'whiteSpace': 'nowrap'})
        ]


if __name__ == '__main__':
    app.run(debug=True)