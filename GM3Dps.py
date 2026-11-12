# -*- coding: utf-8 -*-
"""
Created on Sat Oct 10 10:33:47 2026

@author: yannis
"""

from __future__ import annotations
import numpy as np

class GM3DpsError(ValueError) :
    """
    Error raise by GM3Dps when computation is no longer viable
    """
    

class Figure3D :
    def __init__(self, 
                 width : float, 
                 height : float, 
                 zvector : np.ndarray = np.array([0., -1., 0.]), 
                 origin : np.ndarray = np.array([0., 0., 0.]), 
                 alpha : float = 0.) :
        """
        Base of every figure where everything else will be drawn

        Parameters
        ----------
        width : float
            Screen width of the figure
        height : float
            Screen height of the figure
        zvector : 3D vector, default : [0., -1., 0.]
            Vector facing in the screen (away from the observer)
        origin : 3D vector, default : [0., 0., 0.]
            Point in the center of the screen
        alpha : float
            Rotation (in degrees) of the figure on the screen anticlockwise
        """
        self.children = []
        self.labels = []
        self.width = width
        self.height = height
        self._zvector = zvector/np.linalg.norm(zvector)
        self._alpha = alpha
        self._origin = origin
        self._posmatrixinit()
    
    def _posmatrixinit(self) : #à tester
        xtemp = np.cross(np.array([0., 0., 1.]), self._zvector)
        x = xtemp/np.linalg.norm(xtemp)
        ytemp = np.cross(self._zvector, x)
        y = ytemp/np.linalg.norm(ytemp)
        rot = np.array([[np.cos(self._alpha), np.sin(self._alpha)], 
                        [-np.sin(self._alpha), np.cos(self._alpha)]])
        self._positionmatrix = rot @ np.array([x, y])
        return  self._positionmatrix
    
    def _screen_projection(self, point : np.ndarray) :
        return np.dot(self._positionmatrix, point - self._origin)
        
    
    def export(self, path : str, frame : bool = True) :
        """
        Method to export the figure to a PostScript file

        Parameters
        ----------
        path : str
            Path to save the figure
        frame : bool, default : True
            Whether or not to have frame around the bounding box
        Note
        ----
            Since the extension of the file can be specified in the 
            path, the user can chose between a postscript and an 
            encapsulated postscript file with it.

            But it will not change the heading of the file which eps ready.
        """
        with open(path, 'w') as dest :
            dest.write("%!PS-Adobe-3.0 EPSF-3.0\n%%Creator : GM3Dps\n")
            dest.write("%%BoundingBox : {} {} {} {}\n"
                       .format(300-self.width/2, 
                               421-self.height/2, 
                               self.width, 
                               self.height)) #centered bbox
            dest.write("300 421 translate\ngsave\n") #center the figure
            if frame : 
                dest.write("newpath {} dup 2 div neg {} dup 2 div neg 2 index exch moveto 2 index 0 rlineto exch 0 exch pop exch rlineto neg 0 rlineto closepath stroke\n".format(self.width, self.height))
            for label in self.labels :
                label._export(dest)
            for child in self.children :
                child._export(dest)
            dest.write("grestore\n")
            dest.write("showpage")
    
    def plane2D(self, *args, **kwargs) :
        """
        Method to create :obj:`Plane2D` with the figure as its master

        à compléter
        """
        return Plane2D(self, *args, **kwargs)
            
    def label(self, *args, **kwargs) :
        """
        Method to create :obj:`Label` with the figure as its master

        à completer
        """
        return Label(self, *args, **kwargs)

class Label :
    def __init__(self, 
                 master : Figure3D, 
                 text : str, 
                 origin : np.ndarray, 
                 offset2D : np.ndarray = np.array([0.,0.]), **kwargs) :
        """
        Label to have text on the figure

        Parameters
        ----------
        master : :obj:`Figure3D`
            Where to draw the label
        text : str
            Text to have on the label
        origin :
            3D coordinates of the label (bottom left)
        offset2D :
            Screen offset to apply on the label
        **kwargs :
            Arguments passed down to style
        """
        self.text = text
        self.master = master
        self.master.labels.append(self)
        self.origin = origin
        self.offset2D = offset2D
        self._drawflag = True
        self.style(**kwargs)
    
    def style(self, font : str = "Times-New-Roman", size : int = 15) :
        """
        Edit the style of the label

        Parameters
        ----------
        font : str, default : "Times-New-Roman"
            Font used by the label
        size : int, default : 15
            Font size used by the label
        """
        self.font = font
        self.size = size

    @property
    def draw(self) :
        return self._drawflag

    @draw.setter
    def draw(self, value : bool) :
        self._drawflag = value
    
    def _drawstyle(self, file) :
        file.write("/{} findfont {} scalefont setfont\n".format(self.font, self.size))
    
    def _export(self, file) :
        if self._drawflag :
            position = self.master._screen_projection(self.origin) + self.offset2D
            file.write("{} {} moveto \n".format(position[0], position[1]))
            self._drawstyle(file)
            file.write("({}) show\n".format(self.text))

class Plane2D :
    def __init__(self, 
                 master : Figure3D, 
                 origin : np.ndarray, 
                 normal : np.ndarray, 
                 alpha : float = 0.) :
        """
        2D plane on the Figure to draw 2D objects

        Parameters
        ----------
        master : :obj:`Figure3D`
            Figure where to have the plane
        origin : 3D Vector
            3D coordinates of the 0, 0 point of the plane
        normal : 3D vector
            Normal vector to the plane (does not need to be a unit vector)
        alpha : float, default : 0.
            Rotation of the plane aroung its normal vector 
            anticlockwise. By default, the second vector of the plane
            will be as vertical as possible upwards
        """
        self.master = master
        self.children = []
        master.children.append(self)
        self.origin = origin
        self.normal = normal
        self.alpha = alpha
        
        #unit vector on the plane
        self._ex = np.array([-normal[1], normal[0], 0.]) #Ez x normal
        self._ex /= np.linalg.norm(self._ex)
        self._ey = np.array([-normal[0]*normal[2], -normal[1]*normal[2], normal[0]**2 + normal[1]**2]).astype(np.float64) #normal x ex
        self._ey /= np.linalg.norm(self._ey)
        self._position_matrix = np.array([self._ex, self._ey])
        
        self._lambda0 = None
        self._lambda1 = None
        self._alpha0 = None
        self._alpha1 = None

    def _position3d(self, coordinates : np.ndarray) :
        return np.matvec(self._position_matrix.T, coordinates) + self.origin
    
    def _coordinate(self, file) :
        file.write("{} {} translate\n".format(self.origin[0], self.origin[2]))
        
        #matrix computing
        if self._lambda0 == None :
            ex = np.dot(self.master._positionmatrix, self._ex)
            ey = np.dot(self.master._positionmatrix, self._ey)
            M= np.array([ex, ey]).T
            D0, R0 = np.linalg.eig(M.T@M)
            D1, R1 = np.linalg.eig(M@M.T)
            D0 = np.real(D0)
            D1 = np.real(D1)
            R0 = np.real(R0)
            R1 = np.real(R1)
        
            if not (np.isclose(D0, D1).all()) :
                R1 = np.array([R1[:,1], R1[:,0]])
            if np.linalg.det(R0) < 0 :
                R0[:,1] = -R0[:,1]
            if np.linalg.det(R1) < 0 :
                R1[:,1] = -R1[:,1]
        
            self._lambda0 = np.dot(R1.T@M, R0[:,0])[0]
            self._lambda1 = np.dot(R1.T@M, R0[:,1])[1]
            self._alpha0 = -np.atan2(-R0[0,1], R0[0,0])
            self._alpha1 = np.atan2(-R1[0,1], R1[0,0])
        
        file.write("{} rotate\n".format(np.rad2deg(self._alpha1)))
        file.write("{} {} scale\n".format(self._lambda0, self._lambda1))
        file.write("{} rotate\n".format(np.rad2deg(self._alpha0)))
        file.write("{} rotate\n".format(np.rad2deg(self.alpha)))
    
    def _export(self, file) :
        self._coordinate(file)    
        for child in self.children :
            child._export(file)
        file.write("grestore\n")

    def point(self, *args, **kwargs) :
        """
        Method to create a :obj:`Point2D` on the plane

        à compléter
        """
        return Point2D(self, *args, **kwargs)
    
    def line(self, *args, **kwargs) :
        """
        Method to create a :obj:`Line2D` on the plane

        à compléter
        """
        return Line2D(self, *args, **kwargs)
    
    def polygon(self, *args, **kwargs) :
        """
        Method to create a :obj:`Polygon2D` on the plane

        à compléter
        """
        return Polygon2D(self, *args, **kwargs)
    
    def rectangle(self, *args, **kwargs) :
        """
        Method to create a :obj:`Rectangle2D` on the plane

        à compléter
        """
        return Rectangle2D(self, *args, **kwargs)
    
    def ellipse(self, *args, **kwargs) :
        """
        Method to create an :obj:`Ellipse2D` on the plane

        à compléter
        """
        return Ellipse2D(self, *args, **kwargs)
    
    def arc(self, *args, **kwargs) :
        """
        Method to create an :obj:`Arc2D` on the plane

        à compléter
        """
        return Arc2D(self, *args, **kwargs)
    
    def angle(self, *args, **kwargs) :
        """
        Method to create an :obj:`Angle2D` on the plane

        à compléter
        """
        return Angle2D(self, *args, **kwargs)
    
    def _arrowhead(self, *args, **kwargs) :
        return _ArrowHead2D(self, *args, **kwargs)
    

class _Object2D :
    def __init__(self, master : Plane2D) :
        self.master = master
        self._drawflag = False
        self._dash = None
        master.children.append(self)
        self._label_position = np.array([0., 0.])
    
    def style(self, dash : list[float|int] =None) :
        if dash != None :
            self._dash = dash.copy()
        
    def _drawstyle(self, file) :
        if self._dash != None :
            file.write("[")
            for e in self._dash :
                file.write("{} ".format(e))
            file.write("] 0 setdash\n")
        else :
            file.write("[] 0 setdash\n")
            
    
    def draw(self) :
        self._drawflag = True
    
    def undraw(self) :
        self._drawflag = False

    def label(self, 
              text : str, 
              offset3d : np.ndarray=np.array([0., 0., 0.]), 
              offset2d : np.ndarray=np.array([0., 0.]),
              **kwargs) :
        return Label(self.master.master, 
                     text, 
                     self.master._position3d(self._label_position)+offset3d,
                     offset2d, 
                     **kwargs)
    
    def _export(self, file) :
        return
    

class Point2D(_Object2D) :
    @staticmethod
    def _compatibilitycheck(master, pointlike) :
        if isinstance(pointlike, Point2D) :
            return pointlike
        elif isinstance(pointlike, np.ndarray) :
            return Point2D(master, pointlike)
        elif isinstance(pointlike, np.ndarray) :
            return Point2D(master, np.array(pointlike))
        else :
            raise TypeError("expected Point2D, numpy ndarray or list got {} instead".format(type(pointlike)))
    
    def __init__(self, master : Plane2D, pos : np.ndarray) :
        """
        2D point on a plane

        Parameters
        ----------
        master : :obj:`Plane2D`
            Plane on which the point will be placed
        pos : 2D Vector
            Position on the point on the plane
        """
        self._position = pos
        super().__init__(master)
        self._label_position = pos

    @property
    def position(self) :
        return self._position

    @position.setter
    def position(self, pos) :
        self._position = pos
        self._label_position = pos
    
    def line(self, end : np.ndarray|Point2D) :
        """
        Create a line between the point and another one

        Parameters
        ----------
        end : :obj:`Point2D`
            End of the line to draw

        Returns
        -------
        :obj:`Line2D`
            Line between the two points
        """
        return Line2D(self.master, self, end)
    
    def __sub__(self, other : Point2D|np.ndarray) :
        if isinstance(other, Point2D) :
            return self.position - other.position
        else :
            return self.position - other

class Line2D(_Object2D):
    def __init__(self, 
                 master : Plane2D, 
                 origin : np.ndarray|Point2D, 
                 end : np.ndarray|Point2D) :
        """
        Line to draw on a 2D plane

        Parameters
        ----------
        master : :obj:`Plane2D`
            Plane on which the line will be drawn
        origin : :obj:`Point2D`
            Start of the line
        end : :obj:`Point2D`
            End of the line
        """
        super().__init__(master)
        self._start = Point2D._compatibilitycheck(master, origin)
        self._end = Point2D._compatibilitycheck(master, end)
        self._label_position = (self._end._position + self._start._position)/2

    @property
    def end(self) :
        return self._end

    @end.setter
    def end(self, end : Point2D) :
        self._end = end
        self._label_position = (self._end._position + self._start._position)/2

    @property
    def start(self) :
        return self._start

    @start.setter
    def start(self, start : Point2D) :
        self._start = start
        self._label_position = (self._end._position + self._start._position)/2
    
    def _export(self, file) :
        if self._drawflag :
            self._drawstyle(file)
            file.write("newpath {} {} moveto {} {} lineto stroke\n".format(self.start.position[0], self.start.position[1], self.end.position[0], self.end.position[1]))
    
    def intersection(self, other : Line2D) :
        """
        Compute the intersection of two lines on the same plane

        Parameters
        ----------
        other : :obj:`Line2D`
            Other line with which to compute the intersection
        
        Returns
        -------
        :obj:`Point2D`
            Point of the intersection of the two lines
        """
        a, b = (self.end - self.start)[0], (self.end - self.start)[1]
        c, d = (other.end - other.start)[0], (other.end - other.start)[1]
        v0 = np.array([b, -a])
        v1 = np.array([d, -c])
        e = np.dot(self.start.position, v0)
        f = np.dot(other.start.position, v1)
        return self.master.point(np.linalg.solve(np.array([v0, v1]), 
                                                 np.array([e,f])))
    
    def angle(self, other : Line2D, **kwargs) :
        """
        Return an angle object to show the angle between to lines

        Parameters
        ----------
        other : :obj:`Line2D`
            Other line to draw the angle with
        **kwargs :
            Arguments passed down to :obj:`Angle2D`
        
        Returns
        -------
        :obj:`Angle2D`
            Angle between the two lines
        """
        center = self.intersection(other)
        v0 = self.end - self.start
        v1 = other.end - other.start
        alpha0 = np.atan2(v0[1], v0[0])
        alpha1 = np.atan2(v1[1], v1[0])
        return self.master.angle(center, alpha0, alpha1, 15., **kwargs)
            

class Polygon2D(_Object2D) :
    def __init__(self, master : Plane2D, 
                 verteces : list[np.ndarray]|list[Point2D]) :
        """
        Polygon on a 2D plane

        Parameters
        ----------
        master : :obj:`Plane2D`
            Plane on which to plot the polygon
        verteces : list[:obj:`Point2D`]
            Verteces of the polygon
        """
        n = len(verteces)
        self.verteces = n*[None]
        self.edges = n*[None]
        for i in range(n) :
            self.verteces[i] = Point2D._compatibilitycheck(master, verteces[i])
        super().__init__(master)
        for i in range(n) :
            self.edges[i] = self.verteces[i].line(self.verteces[i-n+1])
        temp = [pt._position for pt in self.verteces]
        self._label_position = np.mean(temp, axis=0)
        
    def draw(self) :
        super().draw()
        for edge in self.edges:
            edge.draw()
    
    def undraw(self) :
        super().undraw()
        for edge in self.edges:
            edge.undraw()
    
    def style(self, *args, **kwargs) :
        super().style(*args, **kwargs)
        for edge in self.edges:
            edge.style(*args, **kwargs)
            

class Rectangle2D(Polygon2D) :
    def __init__(self, master : Plane2D, 
                 point0 : np.ndarray|Point2D, 
                 point1 : np.ndarray|Point2D, 
                 point3 : np.ndarray|Point2D) :
        """
        Rectangle on a 2D plane

        Parameters
        ----------
        master : :obj:`Plane2D`
            Plane on which to plot the rectangle
        point0 : :obj:`Point2D`
            A vertex of the rectangle
        point1 : :obj:`Point2D`
            An adjacent vertex to point0 of the rectangle
        point3 : :obj:`Point2D`
            An other adjacent vertex to point0 of the rectangle
        """
        point3 = Point2D._compatibilitycheck(master, point3)
        point0 = Point2D._compatibilitycheck(master, point0)
        point1 = Point2D._compatibilitycheck(master, point1)
        if np.abs(np.dot(point1 - point0, point3 - point0)) > 1.e-6 :
            raise GM3DpsError("The two sides of the rectangle are not perpendicular to each other")
        super().__init__(master,
                         [point0, 
                          point1,
                          master.point(point1.position + (point3 - point0)),
                          point3])
        

class Ellipse2D(_Object2D) :
    def __init__(self, master : Plane2D, 
                 center : Point2D|np.ndarray, 
                 point0 : Point2D|np.ndarray, 
                 point1 : Point2D|np.ndarray) :
        """
        Ellipse on a 2D plane

        Parameters
        ----------
        master : :obj:`Plane2D`
            Plane on which to plot the ellipse
        center : :obj:`Point2D`
            Center of the ellipse
        point0 : :obj:`Point2D`
            Point at the end of the major axis
        point1 : :obj:`Point2D`
            Point at the end of the minor axis
        """
        self._center = Point2D._compatibilitycheck(master, center)
        self._point0 = Point2D._compatibilitycheck(master, point0)
        self._point1 = Point2D._compatibilitycheck(master, point1)
        self._a = np.linalg.norm(self._point0-self._center)
        self._b = np.linalg.norm(self._point1-self._center)
        if self._a < self._b :
            self._b, self._a = self._a, self._b
            self._point0, self._point1 = self._point1, self._point0
        self._eccentricity = np.sqrt(1-(self._b/self._a)**2)
        if np.abs(np.dot(self._point0-self._center, 
                         self._point1-self._center)) > 1.e-6 :
            raise GM3DpsError("The minor axis and the major axis are not perpendicular to each other")
        super().__init__(master)
        self._label_position = self._center
    
    def _export(self, file) :
        if self._drawflag :
            Maxis = self._point0 - self._center
            alpha = np.rad2deg(np.atan2(Maxis[1], Maxis[0]))
            file.write("{} {} translate ".format(self._center.position[0],
                                                 self._center.position[1]))
            file.write("{} rotate ".format(alpha))
            file.write("1 {} scale\n".format(self._b/self._a))
            self._drawstyle(file)
            file.write("newpath 0 0 {} 0 360 arc stroke\ngrestore\ngsave\n".format(np.linalg.norm(Maxis)))
            self.master._coordinate(file)
    
    def foci(self) :
        """
        Returns the foci of the ellipse

        Returns
        -------
        focus0 : :obj:`Point2D`
            Focus point closest to point0
        focus1 : :obj:`Point2D`
            Focus point furthest to point0
        """
        focus0 = self.master.point(self._center.position+self._eccentricity*(self._point0-self._center))
        focus1 = self.master.point(self._center.position-self._eccentricity*(self._point0-self._center))
        return focus0, focus1
    
    def point(self, alpha : float, mode : str = "eccentric") :
        """
        Return a point on the ellipse corresponding to an angle.

        Parameters
        ----------
        alpha : float
            Angle to position the point
        mode : str, default ``"eccentric"``
            mode to mesure the angle
                * ``"eccentric"`` : using the eccentric angle to 
                positionthe point, starting from ``point0`` and going 
                towards ``point1``
                
                * ``"true0"`` : using the true anomaly starting from 
                ``point0`` going towards ``point1``
                
                * ``"true1"`` : using the true anomaly starting from 
                the opposite point to ``point0`` and going the same way 
                as ``"true0"``
        
        Returns
        -------
        out : :obj:`Point2D`
            Corresponding to the angle
        """
        if mode == "eccentric" :
            return self.master.point(np.cos(alpha)*(self._point0-self._center) + np.sin(alpha)*(self._point1-self._center))
        elif mode == "true0" :
            theta = 2.*np.atan2(np.sqrt((1.-self._eccentricity)/(1.+self._eccentricity))*np.sin(alpha/2.),np.cos(alpha/2.))
            return self.point(theta, mode="eccentric")
        elif mode == "true1" :
            theta = 2.*np.atan2(np.sqrt((1.-self._eccentricity)/(1.+self._eccentricity))*np.sin(alpha/2.),np.cos(alpha/2.)) + np.pi
            return self.point(theta, mode="eccentric")
        else :
            raise GM3DpsError("mode should be eccentric, true0 or true1 recieved {} instead".format(mode))


class _ArrowHead2D(_Object2D) :
    def __init__(self, master : Plane2D, end : Point2D|np.ndarray, length : float, width : float, alpha : float) :
        super().__init__(master)
        self._end = Point2D._compatibilitycheck(master, end)
        self.length = length
        self.width = width
        self.alpha = alpha
        self._label_position = self._end._position

    @property
    def end(self) :
        return self._end

    @end.setter
    def end(self, end : Point2D) :
        self._end = end
        self._label_position = self.end._position
    
    def _export(self, file) :
        if self._drawflag :
            file.write("{} {} moveto\n".format(self.end.position[0], self.end.position[1]))
            file.write("{} dup rotate\n".format(np.rad2deg(self.alpha)))
            self._drawstyle(file)
            file.write("0 {} dup 2 div {} neg exch rlineto neg rlineto closepath fill\nneg rotate\n".format(self.width, self.length))


class Vector2D(_Object2D) :
    def __init__(self, master : Plane2D, 
                 start : Point2D|np.ndarray, 
                 end : Point2D|np.ndarray) :
        """
        Vector to plot on a 2D plane

        Parameters
        ----------
        master : :obj:`Plane2D`
            Plane on which the vector will be plotted
        start : :obj:`Point2D`
            Start of the vector
        end : :obj:`Point2D`
            End of the vector
        """
        super().__init__(master)
        self.start = Point2D._compatibilitycheck(master, start)
        self.end = Point2D._compatibilitycheck(master, end)
        self.line = master.line(self.start, self.end)
        temp = self.end - self.start
        self.arrowhead = master._arrowhead(self.end, 10., 5., np.rad2deg(np.atan2(temp[1], temp[0])))
        self._label_position = self.line._label_position
    
    def draw(self) :
        super().draw()
        self.line.draw()
        self.arrowhead.draw()
    
    def undraw(self):
        super().undraw()
        self.line.undraw()
        self.arrowhead.undraw()
    
    def style(self, *args, **kwargs):
        super.style(*args, **kwargs)
        self.line.style(*args, **kwargs)
        self.arrowhead.style(*args, **kwargs)

class Arc2D(_Object2D) :
    def __init__(self, master : Plane2D, 
                 center : Point2D|np.ndarray, 
                 alpha0 : float, 
                 alpha1 : float, 
                 radius : float) :
        """
        Arc to show an angle on a 2D plane

        Parameters
        ----------
        master : :obj:`Plane2D`
            Plane to plot the arc on
        center : :obj:`Point2D`
            Center of the arc
        alpha0 : float
            Start of the arc
        alpha1 : float
            End of the arc
        radius : float
            Radius of the arc
        """
        super().__init__(master)
        self.center = Point2D._compatibilitycheck(self.master, center)
        self.radius = radius
        self.alpha0 = alpha0
        self.alpha1 = alpha1
        self._label_position = self.center.position + self.radius*(np.array([np.cos((self.alpha0+self.alpha1)/2), np.sin((self.alpha0+self.alpha1)/2)]))
    
    def _export(self, file) :
        if self._drawflag :
            self._drawstyle(file)
            file.write("newpath {} {} {} {} {} arc stroke\n".format(self.center.position[0], 
                                                                    self.center.position[1], 
                                                                    self.radius, 
                                                                    np.rad2deg(self.alpha0), 
                                                                    np.rad2deg(self.alpha1)))

class Angle2D(_Object2D) :
    def __init__(self, master : Plane2D, 
                 center : Point2D|np.ndarray, 
                 alpha0 : float, 
                 alpha1 : float, 
                 radius : float, 
                 anticlockwise : bool = True) :
        """
        Angle to show an angle on a 2D plane

        Parameters
        ----------
        master : :obj:`Plane2D`
            Plane on which to plot the angle
        center : :obj:`Point2D`
            Center of the angle
        alpha0 : float
            Starting *angle* of the angle
        alpha1 : float
            Ending *angle* of the angle
        radius : float
            Radius of the angle
        anticlockwise : bool, default : ``True``
            Whether or not the angle will anticlockwise
        """
        super().__init__(master)
        master.children.append(self)        
        self.center = Point2D._compatibilitycheck(master, center)
        self._radius = radius
        self.alpha0 = alpha0
        self.alpha1 = alpha1
        self.anticlockwise = anticlockwise
        temp = master.point(center.position+self._radius*np.array([np.cos(alpha1), np.sin(alpha1)]))
        if anticlockwise :
            self.arrowhead = master._arrowhead(temp, 6., 11., alpha1 + np.pi/2)
            self.arc = self.master.arc(self.center, self.alpha0, self.alpha1, self._radius)
        else :
            self.arrowhead = master._arrowhead(temp, 6., 11., alpha1 - np.pi/2)
            self.arc = self.master.arc(self.center, self.alpha1, self.alpha0, self._radius)
        self._label_position = self.arc._label_position

    @property
    def radius(self) :
        return self._radius
        
    @radius.setter
    def radius(self, value : float) :
        self._radius = value
        self.arrowhead.end.position = self.center.position + self._radius*np.array([np.cos(self.alpha1), np.sin(self.alpha1)])
        self.arc.radius = value
        
    def draw(self) :
        super().draw()
        self.arc.draw()
        self.arrowhead.draw()
        
    def undraw(self) :
        super().undraw()
        self.arc.undraw()
        self.arrowhead.undraw()
            

class _ObjectPseudo3D :
    def __init__(self, master : Figure3D, origin : np.ndarray, normal : np.ndarray) :
        self.master = master
        self.origin = origin
        self.plane = Plane2D(master, origin, normal, 0.)
        master.children.append(self.plane)