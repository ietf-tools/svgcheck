#
# The contents of this file comes mainly from code by
# Nevil Brownlee, U Auckland

# imported as wp

'''
Elements not allowed in SVG 1.2:
    https://www.ruby-forum.com/topic/144684
    http://inkscape.13.x6.nabble.com/SVG-Tiny-td2881845.html
  marker
  clipPath

style properties come from the CSS, they are allowed in Tiny 1.2

DrawBerry produces attributes with inkscape:,
'http://www.w3.org/XML/1998/namespace',  # wordle uses this

   e.g. inkscape:label and inkscape:groupmode
DrawBerry and Inkscape seem to use this for layers; don't use it!

XML NameSpaces.  Specified by xmlns attribute,
  e.g. xmlns:inkscape="http://inkscape..." specifies inkscape elements
such elements are prefixed by the namespace identifier,
  e.g. inkscape:label="Background" inkscape:groupmode="layer"

Attributes in elements{} 'bottom lines' added during chek.py testing
'''

elements = {
    'svg':            ('version', 'baseProfile', 'width', 'viewBox',
                       'preserveAspectRatio', 'snapshotTime',
                       'height', 'id', 'role', 'break', 'color-rendering',
                       'fill-rule', '<tbreak>'),
    'desc':           ('id', 'role', 'shape-rendering', 'text-rendering', 'buffered-rendering',
                       'visibility', '<break>'),
    'title':          ('id', 'role', 'shape-rendering', 'text-rendering', 'buffered-rendering',
                       'visibility', '<break>'),
    'path':           ('d', 'pathLength', 'stroke-miterlimit', 'id', 'role', 'fill', 'style',
                       'transform', 'font-size', 'fill-rule', '<tbreak>'),
    'rect':           ('x', 'y', 'width', 'height', 'rx', 'ry',
                       'stroke-miterlimit',
                       'id', 'role', 'fill', 'style', 'transform', 'fill-rule', '<tbreak>'),
    'circle':         ('cx', 'cy', 'r', 'id', 'role', 'fill', 'style', 'transform',
                       'fill-rule', '<tbreak>'),
    'line':           ('x1', 'y1', 'x2', 'y2', 'id', 'role', 'fill', 'transform', 'fill-rule',
                       '<tbreak>'),
    'ellipse':        ('cx', 'cy', 'rx', 'ry',
                       'id', 'role', 'fill', 'style', 'transform', 'fill-rule', '<tbreak>'),
    'polyline':       ('points',
                       'id', 'role', 'fill', 'transform', 'fill-rule', '<tbreak>'),
    'polygon':        ('points',
                       'id', 'role', 'fill', 'style', 'transform', 'fill-rule', '<tbreak>'),
    'solidColor':     ('id', 'role', 'fill', 'fill-rule', '<tbreak>'),
    'textArea':       ('x', 'y', 'width', 'height', 'auto',
                       'id', 'role', 'fill', 'transform', 'fill-rule', '<tbreak>'),
    'text':           ('x', 'y', 'rotate', 'id', 'role', 'fill', 'style', 'transform',
                       'font-size', 'fill-rule', '<tbreak>'),
    'g':              ('label', 'class', 'id', 'role', 'fill', 'style', 'transform',
                       'fill-rule', 'visibility', '<tbreak>'),
    'defs':           ('id', 'role', 'fill', 'fill-rule', '<tbreak>'),
    'use':            ('x', 'y', 'href', 'id', 'role',  'fill', 'transform',
                       'fill-rule', '<tbreak>'),
    'a':              ('id', 'role', 'fill', 'transform', 'fill-rule', 'target',
                       '<tbreak>'),  # Linking
    'tspan':          ('x', 'y', 'id', 'role', 'fill', 'fill-rule', '<tbreak>'),
    'tbreak':         ('id', 'role', '<tbreak>'),


    # 'linearGradient': ('gradientUnits', 'x1', 'y1', 'x2', 'y2',
    #                       'id', 'role', 'fill'),
    # 'radialGradient': ('gradientUnits', 'cx', 'cy', 'r',
    #                       'id', 'role', 'fill'),
    # 'stop':           ('id', 'role', 'fill'),  # Gradients

}

# Elements have a list of attributes (above),
#   need to know what attributes each can have.

# Properties capture CSS info, they have lists of allowable values.
# Attributes have allowed values too;
#   we also need to know which elements they're allowed in.

properties = {
    'about':                 (),  # Allowed values for element attributes,
    'base':                  (),  # including those listed in <tbreak>
    'baseProfile':           (),
    'd':                     (),
    'break':                 (),
    'class':                 (),
    'content':               (),
    'cx':                    ('<number>',),
    'cy':                    ('<number>',),
    'datatype':              (),
    'height':                ('<number>',),
    'href':                  (),
    'id':                    (),
    'label':                 (),
    'lang':                  (),
    'pathLength':            (),
    'points':                (),
    'preserveAspectRatio':   (),
    'property':              (),
    'r':                     ('<number>',),
    'rel':                   (),
    'resource':              (),
    'rev':                   (),
    'role':                  (),
    'rotate':                (),
    'rx':                    ('<number>',),
    'ry':                    ('<number>',),
    'space':                 (),
    'snapshotTime':          (),
    'transform':             (),
    'typeof':                (),
    'version':               (),
    'width':                 ('<number>',),
    'viewBox':               ('<number>',),
    'x':                     ('<number>',),
    'x1':                    ('<number>',),
    'x2':                    ('<number>',),
    'y':                     ('<number>',),
    'y1':                    ('<number>',),
    'y2':                    ('<number>',),

    'stroke':                ('none', '<paint>'),  # Change from I-D
    'stroke-width':          (),  # 'inherit'
    'stroke-linecap':        ('butt', 'round', 'square', 'inherit'),
    'stroke-linejoin':       ('miter', 'round', 'bevel', 'inherit'),
    'stroke-miterlimit':     (),  # 'inherit'
    'stroke-dasharray':      (),  # 'inherit', 'none'
    'stroke-dashoffset':     (),  # 'inherit'
    'stroke-opacity':        (),  # 'inherit'
    'vector-effect':         ('non-scaling-stroke', 'none', 'inherit'),
    'viewport-fill':         ('none', 'currentColor', 'inherit', '<color>'),

    'display':               ('inline', 'block', 'list-item', 'run-in', 'compact',
                              'table', 'inline-table', 'table-row-group',
                              'table-header-group', 'table-footer-group',
                              'table-row', 'table-column-group',
                              'table-column', 'table-cell', 'table-caption',
                              'none', 'inherit'),
    'viewport-fill-opacity': (),  # "inherit"
    'visibility':            ('visible', 'hidden', 'collapse', 'inherit'),
    'image-rendering':       ('auto', 'optimizeSpeed', 'optimizeQuality', 'inherit'),
    'color-rendering':       ('auto', 'optimizeSpeed', 'optimizeQuality', 'inherit'),
    'shape-rendering':       ('auto', 'optimizeSpeed', 'crispEdges',
                              'geometricPrecision', 'inherit'),
    'text-rendering':        ('auto', 'optimizeSpeed', 'optimizeLegibility',
                              'geometricPrecision', 'inherit'),
    'buffered-rendering':    ('auto', 'dynamic', 'static', 'inherit'),

    'solid-opacity':         (),  # 'inherit'
    'solid-color':           ('currentColor', 'inherit', '<color>'),
    'color':                 ('currentColor', 'inherit', '<color>'),

    'stop-color':           ('currentColor', 'inherit', '<color>'),
    'stop-opacity':         (),  # 'inherit'

    'line-increment':      (''),  # 'auto', 'inherit'
    'text-align':          ('start', 'end', 'center', 'inherit'),
    'display-align':       ('auto', 'before', 'center', 'after', 'inherit'),

    'font-size':           (),  # 'inherit'
    'font-family':         ('serif', 'sans-serif', 'monospace', 'inherit'),
    'font-weight':         ('normal', 'bold', 'bolder', 'lighter', 'inherit',
                            '100', '200', '300', '400', '500', '600', '700',
                            '800', '900'),
    'font-style':          ('normal', 'italic', 'oblique', 'inherit'),
    'font-variant':        ('normal', 'small-caps', 'inherit'),
    'direction':           ('ltr', 'rtl', 'inherit'),
    'unicode-bidi':        ('normal', 'embed', 'bidi-override', 'inherit'),
    'text-anchor':         ('start', 'middle', 'end', 'inherit'),
    'fill':                ('none', 'inherit', '<color>'),  # # = RGB val
    'fill-rule':           ('nonzero', 'evenodd', 'inherit'),
    'fill-opacity':        (),  # 'inherit'

    'requiredFeatures': (),
    'requiredFormats': (),
    'requiredExtensions': (),
    'requiredFonts': (),
    'systemLanguage': ()
}

basic_types = {  # Lists of allowed values
    '<color>':   ('black', '#ffffff', '#FFFFFF', 'white', '#000000'),
    '<paint>':   ('none', 'currentColor', 'inherit', '<color>'),
    '<tbreak>':  ('id', 'base', 'lang', 'class', 'rel', 'rev', 'typeof', 'content',
                  'datatype', 'resource', 'about', 'property', 'space', 'fill-rule'),
    '<integer>': ('+',),
    '<number>':  ('+',)
    }

color_default = 'black'

style_properties = ('font-family', 'font-weight', 'font-style',
                    'font-variant', 'direction', 'unicode-bidi', 'text-anchor',
                    'fill', 'fill-rule', 'stroke', 'stroke-width', 'font-size',
                    'fill-opacity', 'stroke-linecap', 'stroke-opacity', 'stroke-linejoin')

# Elements allowed within other elements
svg_child = ('title', 'path', 'rect', 'circle', 'line', 'ellipse',
             'polyline', 'polygon', 'solidColor', 'textArea',
             'text', 'g', 'defs', 'use', 'a', 'tspan', 'desc')
text_child = ('desc', 'title', 'tspan', 'text', 'a')

element_children = {  # Elements allowed within other elements
    'svg':        svg_child,
    'desc':       ('text'),
    'title':      ('text'),
    'path':       ('title', 'desc'),
    'rect':       ('title', 'desc'),
    'circle':     ('title', 'desc'),
    'line':       ('title', 'desc'),
    'ellipse':    ('title', 'desc'),
    'polyline':   ('title', 'desc'),
    'polygon':    ('title', 'desc'),
    'solidColor': ('title', 'desc'),
    'textArea':   text_child,
    'text':       text_child,
    'g':          svg_child,
    'defs':       svg_child,
    'use':        ('title', 'desc'),
    'a':          svg_child,
    'tspan':      text_child + ('tbreak',),  # should allow tbreak as a child
    }


svg_urls = (
    'http://www.w3.org/2000/svg',  # Base namespace for SVG
)

xmlns_urls = (  # Whitelist of allowed URLs
    'http://www.w3.org/2000/svg',  # Base namespace for SVG
    'http://www.w3.org/1999/xlink',  # svgwrite uses this
    'http://www.w3.org/XML/1998/namespace',  # imagebot uses this  -- This is xml:
    )

color_map = {
    'rgb(0,0,0)': 'black',
    #    'rgb(255,255,255)': 'white',
    #    '#fff': 'white'
}

color_threshold = 764  # 764 = 255 + 255 + 254 - BC original value is 381
