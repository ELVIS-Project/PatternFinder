import matplotlib.pyplot as plt
import vis


class PlotDendrogram(object):

    def __init__(self, d_data, graph_settings):
        graph_settings = {
                          'label_connections': True,
                          'connection_string': 'rs',
                          'linkage_type': 'average',
                          'xlabel': 'Analyses',
                          'ylabel': 'Percent Dissimilarity',
                          'title': 'Lassus Duet 2-gram Dissimilarity',
                          'interactive_dendrogram': False,
                          'filename_and_type': VIS_PATH[:-3] + 'three_piece_test.png', # .pdf and .png (default) are the only possible formats
                          'return_data': False
                          }
        self._d_data = d_data
        self._graph_settings = graph_settings

    def run(self):
        plt.figure('Dendrogram') 
        # Add connection annotations if the user asked for them
        if self._graph_settings['label_connections']:
            for i, d in zip(self._d_data['icoord'], self._d_data['dcoord']):
                x = 0.5 * sum(i[1:3])
                y = d[1]
                plt.plot(x, y, self._graph_settings['connection_string'])
                plt.annotate("%.3g" % y, (x, y), xytext=(0, -8), textcoords='offset points',
                             va='top', ha='center')
        # Apply labels. If you want to omit a label, pass an empty string ''.
        plt.xlabel(self._graph_settings['xlabel'])
        plt.ylabel(self._graph_settings['ylabel'])
        plt.title(self._graph_settings['title'])
        # If the user provided a filepath, export as a .png (default) or .pdf.
        if self._graph_settings['filename_and_type'] is not None:
            plt.savefig(self._graph_settings['filename_and_type'])
        # If the user wants an interactive matplotlib dendrogram, make it.
        if self._graph_settings['interactive_dendrogram']:
            plt.show()

dendro = PlotDendrogram(d_data, _graph_settings)
dendro.run()