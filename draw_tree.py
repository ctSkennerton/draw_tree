import sys
import re
from ete3 import Tree, faces, NodeStyle, TreeStyle, TextFace
from ete3.coretype.tree import TreeError
# We will need to create Qt4 items for making our custom polygon
from PyQt4 import QtCore
from PyQt4.QtGui import QGraphicsRectItem, QGraphicsSimpleTextItem, \
QGraphicsPolygonItem, QGraphicsTextItem, QPolygonF, QColor, QPen, QBrush, QFont
import math
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
import csv

# Populate this list with the root node of a clade
# that should be turned into a wedge
grouping_nodes = []

def polygon_name_face(node, *args, **kwargs):
    """create a wedge shaped face in the style of ARB

    Args:
    width (int): size in pixels for the width of the wedge
    height (int): size in pixels for the height of the wedge
    width_percent (float): change the angle of the point of the wedge.
    This must be a number between 0 and 1

    Returns:
    QGraphicsRectItem: The Qt graphics item of the polygon
    """

    n_leaves = len(node.get_leaves())
    closest_leaf_dist = node.get_closest_leaf()[1]
    farthest_leaf_dist = node.get_farthest_leaf()[1]

    base_height = 30
    width = 60
    height = math.log(n_leaves, 2) + base_height

    width_percent = closest_leaf_dist / farthest_leaf_dist

    #print(width, height, width_percent)

    points = [
    (0.0, 0.0), # top left point
    (width, 0.0), # top right point
    (width * width_percent, height), # bottom right point
    (0.0, height), # bottom left point
    (0.0, 0.0) # back to the beginning
    ]
    shape = QPolygonF()
    for i in points:
        shape << QtCore.QPointF(*i)

    ## Creates a main master Item that will contain all other elements
    ## Items can be standard QGraphicsItem
    masterItem = QGraphicsRectItem(0, 0, width, height)

    # Keep a link within the item to access node info
    masterItem.node = node

    # I dont want a border around the masterItem
    masterItem.setPen(QPen(QtCore.Qt.NoPen))

    polygon = QGraphicsPolygonItem(shape, masterItem)
    # Make the wedge grey in color
    polygon.setBrush(QBrush(QColor( '#D3D3D3')))

    # Print the name of the node
    # Center text according to masterItem size
    center = masterItem.boundingRect().center()

    text = QGraphicsSimpleTextItem(node.name)
    text.setParentItem(polygon)

    tw = text.boundingRect().width()
    th = text.boundingRect().height()
    text.setPos(center.x() + tw/2, center.y() - th/2)

    # this is a hack to prevent the name being printed twice
    # we set the node name to blank after we write it with the QGraphicsSimpleTextItem
    # it must be set to a blank string for it not to be printed later
    node.name = ''


    # print the number of collapsed leaves in the polygon
    leaves_count_text = QGraphicsSimpleTextItem('('+str(n_leaves)+')')
    leaves_count_text.setParentItem(polygon)
    leaves_count_text.setFont(QFont('Veranda', 6))
    leaves_count_text.setPos(masterItem.boundingRect().x() + 5, center.y() - leaves_count_text.boundingRect().height()/2)

    polygon.setPos(0, masterItem.boundingRect().y()/1.5)

    return masterItem

def scientific_name_face(node, *args, **kwargs):
    scientific_name_text = QGraphicsTextItem()
    words = node.visual_label.split()
    text = []
    if hasattr(node, 'bg_col'):
        container_div = '<div style="background-color:{};">'.format(node.bgcolor)
        text.append(container_div)
    if len(words) < 2:
        # some sort of acronym or bin name, leave it alone
        text.extend(words)

    elif len(words) > 2:
        if words[0] == 'Candidatus':
            # for candidatus names, only the Candidatus part is italicised
            # name shortening it for brevity
            text.append('<i>Ca.</i>')
            text.extend(words[1:])
        elif re.match('^[A-Z]+$', words[0]):
            # If the first word is in all caps then it is an abreviation
            # so we don't want to italicize that at all
            text.extend(words)
        else:
            # assume that everything after the second word is strain name
            # which should not get italicised
            text.extend(['<i>'+words[0],words[1]+'</i>'])
            text.extend(words[2:])
    else:
        text.extend(['<i>'+words[0],words[1]+'</i>'])

    if hasattr(node, 'bg_col'):
        text.append('</div>')
    scientific_name_text.setHtml(' '.join(text))
    #print(scientific_name_text.boundingRect().width(), scientific_name_text.boundingRect().height())

    # below is a bit of a hack - I've found that the height of the bounding
    # box gives a bit too much padding around the name, so I just minus 10
    # from the height and recenter it. Don't know whether this is a generally
    # applicable number to use
    masterItem = QGraphicsRectItem(0, 0, scientific_name_text.boundingRect().width(), scientific_name_text.boundingRect().height() - 10)


    scientific_name_text.setParentItem(masterItem)
    center = masterItem.boundingRect().center()
    scientific_name_text.setPos(masterItem.boundingRect().x(), center.y() - scientific_name_text.boundingRect().height()/2)
    # I dont want a border around the masterItem
    masterItem.setPen(QPen(QtCore.Qt.NoPen))


    return masterItem

def master_ly(node):
    style = NodeStyle()
    style['shape'] = 'circle'

    if hasattr(node,'bgcolor'):
        style['bgcolor'] = node.bgcolor

    if node.is_leaf():
        F = faces.DynamicItemFace(scientific_name_face)
        faces.add_face_to_node(F, node, 0)
        style['size'] = 0
    else:
        if node.support > 1.0:
            node.support /= 100
        if node.support >= .90:
            style['size'] = 5
            style['fgcolor'] = 'black'
        elif node.support >= .70:
            style['size'] = 5
            style['fgcolor'] = 'grey'
        else:
            style['size'] = 0

    if node in grouping_nodes:
        style['draw_descendants'] = False
        # Create an ItemFAce. First argument must be the pointer to
        # the constructor function that returns a QGraphicsItem. It
        # will be used to draw the Face. Next arguments are arbitrary,
        # and they will be forwarded to the constructor Face function.
        # in this case we pass through the width, height, and width_percent for
        # the wedge.
        F = faces.DynamicItemFace(polygon_name_face)
        faces.add_face_to_node(F, node, 0)


    node.set_style(style)

def get_lca(t, nodes):
    outg = t.get_common_ancestor(nodes)
    if outg == t:
        # this is the root node
        t.set_outgroup(t.get_midpoint_outgroup())
        try:
            outg = t.get_common_ancestor(nodes)
        except TreeError:
            print("cannot find the common ancestor of {}".format(nodes), file=sys.stderr)
            return None
    return outg

def set_groups(t, config):
    try:
        for group in config['groups']:
            lca = get_lca(t, group['lca'])
            if lca:
                lca.name = group['name']
                grouping_nodes.append(lca)
    except KeyError:
        pass

def set_outgroup(t, config):
    try:
        outgroup = config['outgroup']
    except KeyError:
        pass
    else:
        if isinstance(outgroup, list):
            # assume that a list of leaves is given
            # outgroup is the lca of these nodes
            lca = get_lca(t, outgroup)
            if lca:
                t.set_outgroup(lca)
        elif isinstance(outgroup, str):
            if outgroup == 'midpoint':
                t.set_outgroup(t.get_midpoint_outgroup())
            else:
                # assume that a single leaf has been given
                # as the outgroup
                t.set_outgroup(t & outgroup)

def set_highlights(t, config):
    try:
        highlights = config['highlight']
    except KeyError:
        return

    for highlight_data in highlights:
        if 'color' not in highlight_data:
            raise ValueError("You must specify a color for highlights")

        try:
            lca_node = get_lca(t, highlight_data['lca'])
            lca_node.add_feature('bgcolor', highlight_data['color'])
        except KeyError:
            pass

        try:
            for leaf_name in highlight_data['leaves']:
                try:
                    l = t & leaf_name
                except TreeError:
                    print("Cannot find leaf with ID {} in tree".format(leaf_name))
                else:
                    l.add_feature('bgcolor', highlight_data['color'])
        except KeyError:
            pass

        try:
            annotation_file_data = highlight_data['annotation_file']
            try:
                column = annotation_file_data['column']
            except KeyError:
                raise ValueError('When highlighting from the annotation file, you must specify which column using the "column" key')

            try:
                regex = annotation_file_data['match']
            except KeyError:
                raise ValueError('When highlighting from the annotation file, you must specify how to search each column using the "match" key')

            for leaf in t.iter_leaves():
                try:
                    leaf_annot = getattr(leaf, column)
                except AttributeError:
                    print("leaf {} has no attribute {}, therefore cannot determine highlighting status".format(leaf.name, column), file=sys.stderr)

                if re.search(regex, leaf_annot):
                    leaf.add_feature('bgcolor', highlight_data['color'])
        except KeyError:
            pass



if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--tree', help='input tree in newick format',required=True)
    parser.add_argument('-a', '--annotations', help='a csv formatted file containing annotations for each leaf. There must be a header row and there must be a column called "Id" which is a match for the leaf name in the tree file.', required=True)
    parser.add_argument("-o", '--output', help='name of the output image file')
    parser.add_argument("-c", "--config", help="yaml formatted file containing config", required=True)

    args = parser.parse_args()

    t = Tree(args.tree)

    with open(args.config) as fp:
        config_data = yaml.load(fp, Loader=Loader)

    if args.annotations is not None:
        id_col = config_data['leaf_name_column']
        with open(args.annotations) as fp:
            csvreader = csv.DictReader(fp)
            for row in csvreader:
                try:
                    node = t & row[id_col]
                except TreeError:
                    pass
                else:
                    visual_label = config_data['visual_label'].format(**row)
                    node.add_feature('visual_label', visual_label)
                    for k, v in row.items():
                        if k != id_col:
                            node.add_feature(k, v)

        set_outgroup(t, config_data)
        set_groups(t, config_data)
        set_highlights(t, config_data)

        for leaf in t.iter_leaves():
            if not hasattr(leaf, 'visual_label'):
                print("cannot find leaf {} in annotations".format(leaf.name))
                leaf.add_feature('visual_label', leaf.name)



    ts = TreeStyle()
    ts.show_leaf_name = False
    ts.layout_fn = master_ly
    #ts.scale = 400 # make the tree wider

    # order the subtrees in ascending order
    t.ladderize(1)

    t.render(args.output, tree_style=ts)
