import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import matplotlib as mpl
import numpy as np


def plot_london(gdf, edgecolour='grey', facecolour='none', missingcolour='grey', linewidth=0.3, col=None, borough=False, legend=True,
                return_mappable=False,  leg_label='', leg_ticks=None, cmap='RdYlGn', norm=None, ax=None):
    if ax==None:
        ax = plt.gca()

    if col==None:
        gdf.plot(ax=ax,
                edgecolor=edgecolour, 
                facecolor=facecolour,
                linewidth=linewidth,
                missing_kwds={'color':missingcolour})
    else:
        gdf.plot(ax=ax,
                column=col,
                linewidth=linewidth,
                cmap=cmap,
                norm=norm,
                legend=False,
                missing_kwds={'color':missingcolour})
    if borough and gdf.columns.str.contains('BOROUGH', case=False).any():
        for _, row in gdf.iterrows():
            ax.text(s=row['BOROUGH'][:3].upper(),
                        x=row['LONG'], y=row['LAT'],
                        horizontalalignment='center',
                        fontsize=10,
                        alpha=0.8,
                        path_effects=[pe.withStroke(linewidth=3, foreground="white")])
    ax.set_aspect(1.0 / np.cos(np.radians(51.5)))  # London's latitude
    ax.set_xlim(-0.53, 0.43)
    ax.set_ylim(51.28, 51.72)
    ax.axis('off')

    if legend and col!=None:
        mappable = mpl.cm.ScalarMappable(cmap=cmap, norm=norm)
        if leg_ticks is not None:
            cbar = plt.colorbar(mappable, ax=ax, ticks=leg_ticks, format='%.0f', label=leg_label)
            cbar.set_ticklabels([f'{int(t)}' for t in leg_ticks])
        else:
            cbar = plt.colorbar(mappable, ax=ax, label=leg_label)
    
    if return_mappable:
        mappable = mpl.cm.ScalarMappable(cmap=cmap, norm=norm)
        return mappable



def highlight_area(gdf, area_list, col_name, colour='grey', alpha=0.5, ax=None):
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