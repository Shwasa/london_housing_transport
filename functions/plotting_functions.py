import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import matplotlib as mpl
from matplotlib.colors import LinearSegmentedColormap
import folium
import numpy as np

# PLOT LONODN MAP
def plot_london(gdf, edgecolour='grey', facecolour='none', missingcolour='grey', linewidth=0.3, col=None, borough=False, legend=True,
                return_mappable=False,  leg_label='', leg_ticks=None, cmap='RdYlGn', cmap_bins=256, norm=None, ax=None):
    
    """Plots a map of London using a GeoDataFrame of polygons, with optional choropleth colouring, borough labels, and legend.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        GeoDataFrame containing London geometries (polygons or multipolygons).

    edgecolour : str, optional (default='grey')
        Colour of polygon borders.

    facecolour : str, optional (default='none')
        Fill colour for polygons when no choropleth column is given.

    missingcolour : str, optional (default='grey')
        Fill colour for geometries with missing (NaN) data.

    linewidth : float, optional (default=0.3)
        Width of polygon borders.

    col : str or None, optional (default=None)
        Column to use for choropleth. If None, outlines only are drawn.

    borough : bool, optional (default=False)
        If True, labels boroughs using the first 3 letters of the 'BOROUGH' column.

    legend : bool, optional (default=True)
        If True, displays a colourbar when plotting a choropleth.

    return_mappable : bool, optional (default=False)
        If True, returns the Matplotlib `ScalarMappable` for custom legends.

    leg_label : str, optional (default=None)
        Label for the colourbar legend.

    leg_ticks : list or None, optional (default=None)
        Tick positions for the colourbar.

    cmap : str, optional (default='RdYlGn')
        Matplotlib colormap name for choropleth colours.
    
    cmap_bins : int, optional (default=256)
        Number of bins for colormap, default to full 256.

    norm : matplotlib.colors.Normalize or None, optional (default=None)
        Normalisation for colour scaling. If None, computed from min/max of data.

    ax : matplotlib.axes.Axes or None, optional (default=None)
        Axis to plot on. If None, uses current axis.

    Returns
    -------
    None or matplotlib.cm.ScalarMappable
        Returns the mappable object if `return_mappable=True`.

    """
        
    if ax is None:
        ax = plt.gca()

    # plot outlines
    if col is None:
        gdf.plot(ax=ax,
                edgecolor=edgecolour, 
                facecolor=facecolour,
                linewidth=linewidth,
                missing_kwds={'color':missingcolour})
        mappable = None
    
    # plot choropleth
    else:
        # determine norm
        if norm is None:
            vmin, vmax = gdf[col].min(), gdf[col].max()
            norm = plt.Normalize(vmin=vmin, vmax=vmax)
        
        # binned cmap
        binned_cmap = LinearSegmentedColormap.from_list('cmap_name', plt.get_cmap(cmap)(np.linspace(0, 1, 256)), N=cmap_bins)

        gdf.plot(ax=ax,
                column=col,
                linewidth=linewidth,
                cmap=binned_cmap,
                norm=norm,
                legend=False,
                missing_kwds={'color':missingcolour})
        mappable = mpl.cm.ScalarMappable(cmap=binned_cmap, norm=norm)
    
    # plot borough lines
    if borough and gdf.columns.str.contains('BOROUGH', case=False).any():
        for _, row in gdf.iterrows():
            x, y = row['geometry'].centroid.x, row['geometry'].centroid.y # find centroids
            ax.text(s=row['BOROUGH'][:3].upper(),
                    x=x,
                    y=y,
                    horizontalalignment='center',
                    fontsize=8,
                    alpha=0.8,
                    path_effects=[pe.withStroke(linewidth=3, foreground="white")])
    ax.set_aspect(1.0 / np.cos(np.radians(51.5)))  # London's latitude
    ax.set_xlim(-0.53, 0.43)
    ax.set_ylim(51.28, 51.72)
    ax.axis('off')

    # add colourbar
    if legend and mappable is not None:
        if leg_ticks:
            cbar = plt.colorbar(mappable, ax=ax, ticks=leg_ticks, label=leg_label)
            cbar.set_ticklabels(leg_ticks)
        else:
            plt.colorbar(mappable, ax=ax, label=leg_label)
    
    if return_mappable:
        return mappable


# HIGHLIGHT AREA
def highlight_area(gdf, area_list, col_name, colour='grey', alpha=0.5, ax=None):

    """Highlights selected boroughs or areas within a London GeoDataFrame.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        GeoDataFrame containing a column to match area names (e.g., 'BOROUGH').

    area_list : list of str
        List of area names (partial or full) to highlight.

    col_name : str
        Column name in `gdf` containing area names.

    colour : str, optional (default='grey')
        Fill colour for highlighted polygons.

    alpha : float, optional (default=0.5)
        Transparency of the highlighted areas.

    ax : matplotlib.axes.Axes or None, optional (default=None)
        Axis to plot on. If None, uses current axis."""

    highlighted_gdf = gdf[gdf[col_name].str.contains('|'.join(area_list), case=False)]

    if ax==None:
        ax = plt.gca()
    
    highlighted_gdf.plot(ax=ax, 
                        edgecolor=None, 
                        facecolor=colour,
                        alpha=alpha)

    ax.set_aspect(1.0 / np.cos(np.radians(51.5)))  # London's latitude
    ax.set_xlim(-0.53, 0.43)
    ax.set_ylim(51.28, 51.72)
    ax.axis('off')

# PLOT TRANSPORT
def plot_transport(transport_coords, type_col='TYPE', s=10, colour=None, alpha=0.7, edgecolour='black', linewidths=0.5, ax=None):
    """
    Plots transport station coordinates on an existing London map.

    Parameters
    ----------
    transport_coords: pandas.DataFrame or geopandas.GeoDataFrame
        DataFrame containing at least 'LAT', 'LON', 'NAME', and a transport type column.

    type_col: str, optional (default='TYPE')
        Column name indicating transport mode (e.g. Tube, DLR, etc.).

    s: float, optional (default=10)
        Marker size.
    
    colour: str, optional
        Colour of markers, defaults to separate colours per transport type.

    alpha: float, optional (default=1)
        Transparency level of markers.

    edgecolour: str, optional (default='None')
        Edge colour for markers.

    linewidths: float, optional (default=0.2)
        Edge line width for markers.
    """

    if ax==None:
        ax = plt.gca()

    if colour is not None:
        ax.scatter(x=transport_coords['LON'], y=transport_coords['LAT'], s=s, color=colour, alpha=alpha, edgecolors=edgecolour, linewidths=linewidths, label='Transport')

    else:
        grouped_transport_coords = transport_coords.groupby(type_col)

        transport_names = ['Tube', 'Overground', 'Tram', 'Dlr', 'Elizabeth Line']
        colours = ['blue', 'orange', 'green', 'red', 'purple']

        for i, transport in enumerate(transport_names):
            df = grouped_transport_coords.get_group(transport)
            ax.scatter(x=df['LON'], y=df['LAT'], s=s, color=colours[i], alpha=alpha, edgecolors=edgecolour, linewidths=linewidths, label=transport)


# MAKE AND SAVE INTERACTIVE MAP
def make_interactive_map(main_gdf, columns, borough_gdf=None, filepath='map.html', key='LSOA21CD', cmap='RdYlGn', cmap_bins=250, nan_fill_color='lightgray',
                         leg_label=None, title='Main Map', highlight_cols=None, highlight_aliases=None,
                         transport_coords=None, transport_type_col='TYPE', transport_s=0.5, transport_a=0.8):
    
    """Creates an interactive .html map with optional borough outlines and transport markers.

    Parameters
    ----------
        main_gdf: geopandas.GeoDataFrame
            The main GeoDataFrame used to create the map containing polygons/multipolygons and columns to use visualise choropleth.
        
        columns: list of str
            Columns containing numerical values to form choropleth on.

        borough_gdf: geopandas.GeoDataFrame, optional
            Optional GeoDataFrame containing polygons/multipolygons borough outlines overlay .

        filepath: str, optional (default='map.html')
            Filepath where generated map will be stored. If left empty, default filename is 'map.html'.

        key: str, optional (default='LSOA21CD')
            Column name used to join or index spatial features for mapping containing no duplicate values.

        cmap: str, optional (default='RdYlGn')
            Matplotlib or Folium-compatible colour map used for the choropleth layer.

        cmap_bins: int, optional (default=250)
            Number of discrete bins to use for the choropleth color gradient.

        nan_fill_color: str, optional (default='lightgray')
            Matplotlib or Folium-compatible colour to fill nan values.

        leg_label: str or None, optional (default=None)
            Label to display in the map legend.

        title: str or None, optional (default=None)
            Optional title to display on the map.

        highlight_cols: list of str or None, optional (default=None)
            Additional columns whose values should be displayed interactively in tooltips/popups.

        highlight_aliases: list of str or None, optional (default=None)
            Optional alias names (friendly labels) corresponding to `highlight_cols`.

        transport_coords: geopandas.GeoDataFrame or None, optional (default=None)
            Optional GeoDataFrame of transport station coordinates to overlay (Tube, DLR, etc.).

        transport_type_col: str, optional (default='TYPE')
            Column in `transport_coords` specifying the transport type (for colour coding).

        transport_s : float, optional (default=0.5)
            Marker size scaling factor for transport points.

        transport_a : float, optional (default=0.8)
            Transparency (alpha) for transport point markers.
    
    Returns
    -------
    folium.Map
        A Folium Map object. Saves an `.html` version to disk.
    
    """
    

    # create interactive map
    folium_map = folium.Map(location=(51.515815,-0.064798), tiles='CartoDB Positron', prefer_canvas=True)

    if highlight_cols:
        highlight=True
    else:
        highlight=False

    # convert key and column to right format
    if type(columns) != list:
        columns = [columns]
    columns = [key] + columns
    key_on=f'feature.properties.{key}'

    # LSOA DATA
    geojson_data = main_gdf.to_json()
    choropleth = folium.Choropleth(
        geo_data=geojson_data,
        data=main_gdf,
        key_on=key_on,
        columns=columns,
        fill_color=cmap,
        fill_opacity=0.5,
        line_opacity=0.4,
        line_weight=0.5,
        nan_fill_color=nan_fill_color,
        nan_fill_opacity=0.3,
        legend_name=leg_label,
        name=title,
        highlight=highlight,
        bins=cmap_bins,
        reset=True
    ).add_to(folium_map)

    if highlight_cols:
        folium.features.GeoJsonTooltip(
            fields=highlight_cols,
            aliases=highlight_aliases,
            localize=True,
            style=("background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 5px;")
        ).add_to(choropleth.geojson)

    # BOROUGH
    if borough_gdf is not None:
        borough_geojson_data = borough_gdf.to_json()
        folium.GeoJson(
                borough_geojson_data,
                style_function=lambda feature: {
                "fillColor":'none',
                'fillOpacity': 0,
                "color": "black",
                "weight": 1},
                name='Borough Boundaries',
                interactive=False
        ).add_to(folium_map)

    # TRANSPORT LINKS
    if transport_coords is not None:
        grouped_transport_coords = transport_coords.groupby(transport_type_col)
        transport_names = ['Tube', 'Overground', 'Tram', 'Dlr', 'Elizabeth Line']
        colours = ['blue', 'orange', 'green', 'red', 'purple']

        for i, transport in enumerate(transport_names):
            if transport not in grouped_transport_coords.groups:
                continue
            layer = folium.FeatureGroup(name=transport)
            df = grouped_transport_coords.get_group(transport)
            for _, point in df.iterrows():
                folium.CircleMarker(location=[point.LAT, point.LON],
                                    color=colours[i],
                                    radius=transport_s,
                                    opacity=transport_a,
                                    tooltip=f'{point.NAME}').add_to(layer)
            layer.add_to(folium_map)

    # LAYER CONTROL
    folium.LayerControl().add_to(folium_map)

    if not filepath.endswith('.html'):
        filepath += '.html'
    folium_map.save(filepath)