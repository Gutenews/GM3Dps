# -*- coding: utf-8 -*-
"""
Created on Sat Oct 10 10:33:47 2026

@author: yannis
"""

import numpy as np

class Figure3D :
    def __init__(self, width : float, height : float) :
        self.children = []
        self.width = width
        self.height = height
    
    def export(self, path) :
        with open(path, 'w') as dest :
            dest.write("%!PS-Adobe-3.0 EPSF-3.0\n%%Creator : GM3Dps\n")
            dest.write("%%BoundingBox : {} {} {} {}\n".format(300-self.width/2, 421-self.height/2, self.width, self.height))
            dest.write("300 421 translate\ngsave\n")
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
        
    
    def _export(self, file) :        
        file.write("{} {} translate\n".format(self.origin[0], self.origin[2]))
        
        #matrix computing
        ex = np.array([self._ex[0], self._ex[2]])
        ey = np.array([self._ey[0], self._ey[2]])
        M= np.array([ex, ey]).T
        print(M)
        print(np.dot(M, np.array([1,0])))
        D0, R0 = np.linalg.eig(M.T@M)
        D1, R1 = np.linalg.eig(M@M.T)
        
        if not (np.isclose(D0, D1).all()) :
            R1 = np.array([R1[:,1], R1[:,0]])
        if np.linalg.det(R0) < 0 :
            R0[:,1] = -R0[:,1]
        if np.linalg.det(R1) < 0 :
            R1[:,1] = -R1[:,1]
        
        lambda0 = np.dot(R1.T@M, R0[:,0])[0]
        lambda1 = np.dot(R1.T@M, R0[:,1])[1]
        alpha0 = -np.atan2(-R0[0,1], R0[0,0])
        alpha1 = np.atan2(-R1[0,1], R1[0,0])
        r0 = np.array([[np.cos(alpha0), -np.sin(alpha0)], [np.sin(alpha0), np.cos(alpha0)]])
        r1 = np.array([[np.cos(alpha1), -np.sin(alpha1)], [np.sin(alpha1), np.cos(alpha1)]])
        d =  np.array([[lambda0, 0.], [0., lambda1]])
        print(r1@d@r0)
        
        file.write("{} rotate\n".format(np.rad2deg(alpha1)))
        file.write("{} {} scale\n".format(lambda0, lambda1))
        file.write("{} rotate\n".format(np.rad2deg(alpha0)))
        
        file.write("{} rotate\n".format(np.rad2deg(self.alpha)))
        for child in self.children :
            child._export(file)
        file.write("grestore\n")

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
    
    def _export(self, file) :
        return

class Point2D(_Object2D) :
    def __init__(self, master : Plane2D, pos : np.ndarray) :
        self.position = pos
        super().__init__(master)

class Line2D(_Object2D):
    def __init__(self, master : Plane2D, origin : np.ndarray|Point2D, end : np.ndarray|Point2D) :
        super().__init__(master)
        if isinstance(origin, Point2D) :
            self.start = origin
        else :
            self.start = Point2D(master, origin)
        if isinstance(end, Point2D) :
            self.end = end
        else :
            self.end = Point2D(master, end)
    
    def _export(self, file) :
        if self._drawflag :
            self._drawstyle(file)
            file.write("newpath {} {} moveto {} {} lineto stroke\n".format(self.start.position[0], self.start.position[1], self.end.position[0], self.end.position[1]))

class _ObjectPseudo3D :
    def __init__(self, master : Figure3D, origin : np.ndarray, normal : np.ndarray) :
        self.master = master
        self.origin = origin
        self.plane = Plane2D(master, origin, normal, 0.)
        master.children.append(self.plane)