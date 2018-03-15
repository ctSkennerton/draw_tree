# Drawing nice trees
This script can be used to draw nice looking phylogenetic trees. It's combined with a csv file of annotations for the leaves and a configureation file that can set up the tree for common opperations such as collapsing and highlighting clades.

# Installation
This script is built on [ete3](http://etetoolkit.org/) which must be installed and working 
correctly and additionally requires [pyYAML](http://pyyaml.org/wiki/PyYAMLDocumentation) for 
parsing the configuration file.

# The annotation file
The annotation file is a comma separated values (csv) file where each row contains information
about each leaf in the tree. The file must contain a header row! The column headers must be 
simply named, **no spaces**, **no special characters** are allowed in the column headers.
One of the columns must be the name of the leaf in the tree file

# The configuration file
The configuration file is a [YAML](http://yaml.org/) formatted file that is used to specify
grouping and highlighting of leaves in the tree. The following options are available

## Specifying the outgroup
The outgroup for the tree can be specified by one of three ways. First, a single leaf name
can be used; Second, a list of leaf names can be given, in which case the lowest common
ancestor of the leaves will be used as the node in the tree to root on; third, the word
'midpoint' can be used to specify that the tree should be rooted at the midpoint node 
of the tree.

```
outgroup: 'leaf name'
outgroup: ['leaf name 1', 'leaf name 2', 'leaf name 3']
outgroup: 'midpoint'
```
## Specifying how the annotations match the tree file
The leaf IDs in the tree file have to match up with one one the columns of the annotation file.
In the configuration file give the name of the column in the annotations file that 
corresponds to the leaf name using the `leaf_name_column`

```
leaf_name_column: Id
```

## Give the leaf names some nice formatting
Provide the format for the leaf labels on the tree using
python's [format style](https://docs.python.org/3/library/string.html#formatspec). 
The names of the arguments are based on the annotations file given. In this case the
annotations file will have columns labeled organism and
accession for each leaf:

```
visual_label: '{organism} ({accession})'
```

## Grouping clades
When making large trees it's sometimes a good idea to make the resulting tree image smaller
by drawing some clades as cartoon wedges. These cartoon wedges can be specified using the 
`groups` key, which should contain a list where each item corresponds to a clade to be collapsed.
Each list item (group) should contain a `name` key and an `lca` key. The `lca` key is used 
to specify the lowest common ancestor of a list of leaves.

```
groups:
    -
        name: Firmicutes
        lca:
            - leaf_1
            - leaf_2
    - 
        name: other bacteria
        lca:
            - leaf_3
            - leaf_4

```

## Highlighting clades
Highlighting leaves can be accomplished by adding a `highlight` key to the configuration file.
The data under this key is a list of data for each of the highlighted clades. Highlight data
is required to have a `color` key but may then use any of the three different ways to highlight
the leaves.

```
highlight:
    -
        color: "#FF0000"
        lca: 
            - leaf_1
            - leaf_2
    -
        color: "#00FF00"
        leaves:
            - leaf_3
            - leaf_4
    -
        color: "#0000FF"
        annotation_file:
            column: "taxonomy"
            match: "Proteobacteria"

```

### Using the `lca` key
The `lca` key is for highlighting an entire clade using the lowest common ancestor of a list
of given leaves.

### Using the `leaves` key
The `leaves` key allows you to highlight leaves that may not be monophyletic

### Using the `annotation_file` key
The `annotation_file` key allows you specify highlighting based on the information of the csv formatted annotation file.
You must provide a `column` key with the name of the column in the annotation file to use, and the `match` key which can
be any valid python regular expression.
