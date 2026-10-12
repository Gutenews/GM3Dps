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
    def __init__(self, width : float, height : float) :
        self.children = []
        self.width = width
        self.height = height
    
    def export(self, path) :
        with open(path, 'w') as dest :
            dest.write("%!PS-Adobe-3.0 EPSF-3.0\n%%Creator : GM3Dps\n")
            dest.write("%%BoundingBox : {} {} {} {}\n".format(300-self.width/2, 421-self.height/2, self.width, self.height)) #centering the figure on the paper
            dest.write("300 421 translate\ngsave\n") #centering the figure on the paper
            for child in self.children :
                child._export(dest)
            dest.write("showpage")
            

class Plane2D :
    def __init__(self, master : Figure3D, origin : np.ndarray, normal : np.ndarray, alpha : float) :
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
        
        self.lambda0 = None
        self.lambda1 = None
        self.alpha0 = None
        self.alpha1 = None
        
    def _coordinate(self, file) :
        file.write("{} {} translate\n".format(self.origin[0], self.origin[2]))
        
        #matrix computing
        if self.lambda0 == None :
            ex = np.array([self._ex[0], self._ex[2]])
            ey = np.array([self._ey[0], self._ey[2]])
            M= np.array([ex, ey]).T
            D0, R0 = np.linalg.eig(M.T@M)
            D1, R1 = np.linalg.eig(M@M.T)
        
            if not (np.isclose(D0, D1).all()) :
                R1 = np.array([R1[:,1], R1[:,0]])
            if np.linalg.det(R0) < 0 :
                R0[:,1] = -R0[:,1]
            if np.linalg.det(R1) < 0 :
                R1[:,1] = -R1[:,1]
        
            self.lambda0 = np.dot(R1.T@M, R0[:,0])[0]
            self.lambda1 = np.dot(R1.T@M, R0[:,1])[1]
            self.alpha0 = -np.atan2(-R0[0,1], R0[0,0])
            self.alpha1 = np.atan2(-R1[0,1], R1[0,0])
        
        file.write("{} rotate\n".format(np.rad2deg(self.alpha1)))
        file.write("{} {} scale\n".format(self.lambda0, self.lambda1))
        file.write("{} rotate\n".format(np.rad2deg(self.alpha0)))
        file.write("{} rotate\n".format(np.rad2deg(self.alpha)))
    
    def _export(self, file) :
        self._coordinate(file)    
        for child in self.children :
            child._export(file)
        file.write("grestore\n")

    def point(self, *args, **kwargs) :
        return Point2D(self, *args, **kwargs)
    
    def line(self, *args, **kwargs) :
        return Line2D(self, *args, **kwargs)
    
    def polygon(self, *args, **kwargs) :
        return Polygon2D(self, *args, **kwargs)
    
    def rectangle(self, *args, **kwargs) :
        return Rectangle2D(self, *args, **kwargs)
    
    def ellipse(self, *args, **kwargs) :
        return Ellipse2D(self, *args, **kwargs)
    
    def arrowhead(self, *args, **kwargs) :
        return _ArrowHead2D(self, *args, **kwargs)
    

class _Object2D :
    def __init__(self, master : Plane2D) :
        self.master = master
        self._drawflag = False
        self._dash = None
        master.children.append(self)
    
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
        self.position = pos
        super().__init__(master)
    
    def line(self, end : np.ndarray|Point2D) :
        return Line2D(self.master, self, end)
    
    def __sub__(self, other : Point2D|np.ndarray) :
        if isinstance(other, Point2D) :
            return self.position - other.position
        else :
            return self.position - other

class Line2D(_Object2D):
    def __init__(self, master : Plane2D, origin : np.ndarray|Point2D, end : np.ndarray|Point2D) :
        super().__init__(master)
        self.start = Point2D._compatibilitycheck(master, origin)
        self.end = Point2D._compatibilitycheck(master, end)
    
    def _export(self, file) :
        if self._drawflag :
            self._drawstyle(file)
            file.write("newpath {} {} moveto {} {} lineto stroke\n".format(self.start.position[0], self.start.position[1], self.end.position[0], self.end.position[1]))
            

class Polygon2D(_Object2D) :
    def __init__(self, master : Plane2D, verteces : list[np.ndarray]|list[Point2D]) :
        n = len(verteces)
        self.verteces = n*[None]
        self.edges = n*[None]
        for i in range(n) :
            self.verteces[i] = Point2D._compatibilitycheck(master, verteces[i])
        super().__init__(master)
        for i in range(n) :
            self.edges[i] = self.verteces[i].line(self.verteces[i-n+1])
        
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
    def __init__(self, master : Plane2D, point0 : np.ndarray|Point2D, point1 : np.ndarray|Point2D, point3 : np.ndarray|Point2D) :
        point3 = Point2D._compatibilitycheck(master, point3)
        point0 = Point2D._compatibilitycheck(master, point0)
        point1 = Point2D._compatibilitycheck(master, point1)
        if np.abs(np.dot(point1 - point0, point3 - point0)) > 1.e-6 :
            raise GM3DpsError("The two sides of the rectangle are not perpendicular to each other")
        super().__init__(master, [point0, point1, master.point(point1.position + (point3 - point0)), point3])
        

class Ellipse2D(_Object2D) :
    def __init__(self, master : Plane2D, center : Point2D|np.ndarray, point0 : Point2D|np.ndarray, point1 : Point2D|np.ndarray) :
        self.center = Point2D._compatibilitycheck(master, center)
        self.point0 = Point2D._compatibilitycheck(master, point0)
        self.point1 = Point2D._compatibilitycheck(master, point1)
        if np.abs(np.dot(self.point0-self.center,self.point1-self.center)) > 1.e-6 :
            raise GM3DpsError("The minor axis and the major axis are not perpendicular to each other")
        super().__init__(master)
    
    def _export(self, file) :
        if self._drawflag :
            Maxis = self.point0 - self.center
            maxis = self.point1 - self.center
            alpha = np.rad2deg(np.atan2(Maxis[1], Maxis[0]))
            file.write("{} {} translate ".format(self.center.position[0], self.center.position[1]))
            file.write("{} rotate ".format(alpha))
            file.write("1 {} scale\n".format(np.linalg.norm(maxis)/np.linalg.norm(Maxis)))
            self._drawstyle(file)
            file.write("newpath 0 0 {} 0 360 arc stroke\ngrestore\n".format(np.linalg.norm(Maxis)))
            self.master._coordinate(file)


class _ArrowHead2D(_Object2D) :
    def __init__(self, master : Plane2D, end : Point2D|np.ndarray, back : Point2D|np.ndarray, width : float) :
        super().__init__(master)
        self.end = Point2D._compatibilitycheck(master, end)
        self.back = Point2D._compatibilitycheck(master, back)
        self.width = width
    
    def length(self, length = None) :
        if length :
            self.back.position = self.end.position + length*(self.back-self.end)/np.linalg.norm(self.back-self.end)
        return np.linalg.norm(self.back-self.end)
    
    def _export(self, file) :
        if self._drawflag :
            temp = self.end - self.back
            file.write("{} {} moveto\n".format(self.end.position[0], self.end.position[1]))
            file.write("{} dup rotate\n".format(np.atan2(temp[1], temp[0])))
            self._drawstyle(file)
            file.write("0 {} 2 div dup {} exch rlineto neg rlineto closepath fill\n neg rotate\n".format(self.width, np.linalg.norm(temp)))


class Vector2D(_Object2D) :
    def __init__(self, master : Plane2D, start, end) :
        super().__init__(master)
        self.start = Point2D._compatibilitycheck(master, start)
        self.end = Point2D._compatibilitycheck(master, end)
        self.line = master.line(self.start, self.end)
        self.arrowhead = master.arrowhead(self.end, self.end.position-10.*(self.end-self.start)/np.linalg.norm(self.end-self.start), 6.)
    
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
            

class _ObjectPseudo3D :
    def __init__(self, master : Figure3D, origin : np.ndarray, normal : np.ndarray) :
        self.master = master
        self.origin = origin
        self.plane = Plane2D(master, origin, normal, 0.)
        master.children.append(self.plane)