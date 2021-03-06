from PyQt5.QtWidgets import QApplication, QMainWindow
import sys
sys.path.insert(0, "./ui/")
from ui.pp_ui import Ui_MainWindow
from PyQt5 import QtWidgets
import math
import numpy as np
from shapely.geometry import Polygon
from shapely.geometry import Point
from shapely.geometry import LineString
from descartes import PolygonPatch
import random
import matplotlib.lines as mlines
import matplotlib.pyplot as plt
import copy


class MyPoint(Point):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __add__(self, other):
        return MyPoint(self.x + other.x, self.y + other.y)

    def scale(self, ratio):
        return MyPoint(self.x * ratio, self.y * ratio)

    def getXy(self):
        return (self.x, self.y)

    def rotate(self, theta):
        c, s = np.cos(theta), np.sin(theta)
        r = np.array([[c, -s], [s, c]])
        new_xy = list(np.matmul(r, self.getXy()))
        return MyPoint(new_xy[0], new_xy[1])

class MyLineString(LineString):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def getMyAngle(self):
        return math.atan2(self.coords[1][1] - self.coords[0][1],
                          self.coords[1][0] - self.coords[0][0])

    def getAngle(self, other):
        return math.fabs(self.getMyAngle() - other.getMyAngle())%math.pi


class Obstacle(Polygon):

    def __init__(self, center_point, size = 1):
        self.center = center_point
        corners = [MyPoint(-1, -1), MyPoint(-1, 1), MyPoint(1, 1), MyPoint(1, -1)]
        corners = [p.scale(size) for p in corners]
        new_corners = [c+center_point for c in corners]
        self.p = Polygon([(p.x, p.y) for p in new_corners])
        super().__init__(self.p)

    def getDrawble(self, color):
        return PolygonPatch(self.p, color=color)

    def getCenter(self):
        return self.center

class Robot:
    def __init__(self, start_point, end_point, grid_num, obstacles):
        self.__s_point = start_point
        self.__t_point = end_point
        self.__point_num = grid_num
        self.__obstacles = obstacles
        self.__createStLine()

    def __createStLine(self):
        self.__st_line = MyLineString([self.__s_point.getXy(), self.__t_point.getXy()])
        self.__theta = math.atan2(self.__t_point.y - self.__s_point.y,
                                  self.__t_point.x - self.__s_point.x)
        self.__x_prime_array = np.arange(0, self.__st_line.length+self.__st_line.length/self.__point_num,
                                         self.__st_line.length/self.__point_num)
        self.__points = [MyPoint(x, 0) for x in self.__x_prime_array]
        self.__lines = []

    def setStartStopPoint(self, s_point, t_point):
        self.__s_point = s_point
        self.__t_point = t_point
        self.__createStLine()

    def setObstacles(self, obstacles):
        self.__obstacles = obstacles

    def updatePoints(self, points):
        points = [0]+points+[0]
        self.__points = [MyPoint(x, y).rotate(self.__theta) for x, y in zip(self.__x_prime_array, points)]
        #print("points", [p.getXy() for p in self.__points])
        self.__points = [MyPoint(p.x, p.y) + self.__s_point for p in self.__points]
        #print("points", [p.getXy() for p in self.__points])
        self.__lines = [MyLineString([p1.getXy(), p2.getXy()]) for
                        p1, p2 in zip([self.__s_point] + self.__points,
                                      self.__points+[self.__t_point])]
    

    def getCV(self):
        cv = 0
        for l in self.__lines:
           for obs in self.__obstacles:
                if obs.intersects(l):
                    cv = cv + 1
        return cv

    def getFL(self):
        d = 0
        for l in self.__lines:
            d = d + l.length
        return d

    def getFS(self):
        angles = []
        for i in range(len(self.__lines) - 1):
            angles.append(self.__lines[i].getAngle(self.__lines[i + 1]))
        return max(angles)

    def getFO(self,a):
        #warning this function should be changed
        min_distance = 100000000
        for l in self.__lines:
            for obs in self.__obstacles:
                if l.distance(obs) < min_distance:
                    min_distance = l.distance(obs)         
        return math.exp(-a*min_distance)

    def getCost(self,a):
        cost = self.getFL() + 5*self.getFS() + 30*self.getFO(a) + 10*self.getCV()
        return cost

    # return a line from start to stop
    def getSTLine(self):
        return self.__st_line

    def getStartPoint(self):
        return self.__s_point

    def getEndPoint(self):
        return self.__t_point

    def getPath(self):
        return LineString([p.getXy() for p in self.__points])

    def getTheta(self):
        return self.__theta

    def getObstacles(self):
        return self.__obstacles

class GA:
    #get size of population and chromosome and talent size at the first
    def __init__(self, chSize, talentSize):
        self.__chromosome_size = chSize
        self.__talentSize = talentSize
        self.__population = []
        self.__chromosome = []

    def genPopulation(self,  max, min, population_size):
        self.__population_size = population_size
        self.__population = []
        self.__chromosome = []
        for p in range(self.__population_size):
            self.__population.append(list(np.random.uniform(low = min, high = max, size = self.__chromosome_size)))
        return self.__population

    def getpopulation(self):
        return list(self.__population)
    def setpopulation(self,population):
        self.__population = population

    def mutation(self, population, min, max, num):
        for i in range(num):        
            cop = np.random.randint(low = 0, high = population_size , size=1)
            chromosom = population[cop[0]]
            gene = np.random.randint(0, self.__chromosome_size, 1)
            chromosom[gene[0]]= np.random.uniform(min, max, 1)


    def crossOver(self, population, num):
        #cross_over_point
        for i in range(num):    
            parents = list(np.random.randint(low = 0, high = len(population) , size=2)) 
            parent1 = population[parents[0]]
            parent2 = population[parents[1]]
            cop = list(np.random.randint(low = 0, high = self.__chromosome_size , size=2))
            parent1[cop[0]: cop[1]], parent2[cop[0]: cop[1]] =\
            parent2[cop[0]: cop[1]], parent1[cop[0]: cop[1]]

    def sortPopulation(self,population,robot):
        cost = []
        for chromosome in population:
            robot.updatePoints(chromosome)
            cost.append(robot.getCost(a))
        pop_cost = list(zip(population, cost))
        pop_cost_sorted = list(sorted(pop_cost,key=lambda l:l[1], reverse=False))
        return pop_cost_sorted





#create robot object
num_of_runs = 0
grid_size = 10
obsNum = 30
population_size=50
a=1
best_costs = []
ga = GA(chSize = grid_size, talentSize = 3)
r = Robot(MyPoint(0, 0), MyPoint(10, 10), grid_size + 1, None)
ga.genPopulation(max=5, min=-5,population_size = population_size)
obstacles = [Obstacle(MyPoint(random.randint(1, 20), random.randint(1, 10)), 0.5) for i in
                 range(obsNum)]
r.setObstacles(obstacles)             


# function that they are connected to buttons of user interface

def run(num):
    global num_of_runs 
    
    print("run")
    ga.genPopulation(max=5, min=-5,population_size = population_size)
    best_costs.append([])
    for i in range(num):
        best_costs[num_of_runs].append(iterate()) 
    num_of_runs += 1

    

def result(ui):
    print("show_result")
    best_costs.append([])
    for i in range(len(best_costs[0])):
        sum=0
        for j in range(num_of_runs):
            sum = sum + best_costs[j][i]
        best_costs[len(best_costs)-1].append(sum/num_of_runs) 
    
    fig, ax = plt.subplots(2, int((len(best_costs)+1)/2))
    fig.suptitle("result")
    ax = ax.reshape(-1, 1)
    for a, i in zip(ax, range(len(best_costs))):
        a[0].plot(best_costs[i])
        a[0].grid(which='both')
        if i != len(best_costs) - 1:
            a[0].set_title("run" )
        else:
            a[0].set_title("ave")
    plt.show()




def iterate():
    print("iterate")
    pop = ga.getpopulation()
    sorted_pop_cost = ga.sortPopulation(pop,r)
    print("before")
    print(sorted_pop_cost[0][1],sorted_pop_cost[population_size-1][1])
    sorted_pop, _ = list(zip(*sorted_pop_cost))
    childs = list(copy.deepcopy(sorted_pop))
    # do cross over on childs
    ga.crossOver(childs,int(population_size/4))
    # do mutation
    ga.mutation(childs,-5,5,int(population_size/2))
    # concat and sort parents and childs
    childs_parents = childs + pop
    sorted_childs_parents = ga.sortPopulation(childs_parents, r)
    print("mid")
    print(sorted_childs_parents[0][1],sorted_childs_parents[2* population_size -1][1])
    # select between childs and parents for next generation
    new_Population_cost = sorted_childs_parents[:population_size]
    print("after")
    print(new_Population_cost[0][1],new_Population_cost[population_size-1][1])
    new_population, _ = list(zip(*new_Population_cost))
    r.updatePoints(new_population[0])

    print("FL:{},FS:{},FO:{},CV:{}".format(r.getFL(),r.getFS(),r.getFO(a),r.getCV()))
    form.show_all(r)
    ga.setpopulation(new_population)
    return new_Population_cost[0][1]

        




#Ui class
class Ui(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.setupUi(self)
        self.run.clicked.connect(lambda: run(int(self.num_of_run.text())))
        self.reset_obstacles.clicked.connect(lambda: self.reset_obstacle(r))
        self.set_points.clicked.connect(lambda: self.set_point(r))
        self.iterate.clicked.connect(lambda: iterate())
        self.result.clicked.connect(lambda: result(self))
        self.widget.canvas.ax.grid(b=None, which='both', axis='both')
    
    def show_all(self,robot):
        obstacles=robot.getObstacles()
        p = robot.getPath()
        self.widget.canvas.ax.clear()
        self.widget.canvas.ax.grid(b=None, which='both', axis='both')
        for obs in obstacles:
            self.widget.canvas.ax.add_patch(obs.getDrawble("red"))
        self.widget.canvas.ax.plot([r.getStartPoint().x], [r.getStartPoint().y], 'ro', color = "blue"),
        self.widget.canvas.ax.annotate("start", xy=(r.getStartPoint().x, r.getStartPoint().y), xytext = (r.getStartPoint().x, r.getStartPoint().y + 0.2))
        self.widget.canvas.ax.plot([r.getEndPoint().x], [r.getEndPoint().y], 'ro', color = "blue")
        self.widget.canvas.ax.annotate("end", xy=(r.getEndPoint().x, r.getEndPoint().y), xytext = (r.getEndPoint().x, r.getEndPoint().y + 0.2))
        self.widget.canvas.ax.autoscale(enable=True, axis='both', tight=None)
        self.widget.canvas.ax.autoscale(enable=True, axis='both', tight=None)
        self.widget.canvas.ax.add_line(
            mlines.Line2D([p.coords[i][0] for i in range(len(p.coords))], [p.coords[i][1] for i in range(len(p.coords))],
                        color="green"))
        self.widget.canvas.ax.autoscale(enable=True, axis='both', tight=None)
        self.widget.canvas.draw()

    def set_point(self,robot):
        p = robot.getPath()
        robot.setStartStopPoint(MyPoint(float(self.start_x.text()), float(self.start_y.text())),
                            MyPoint(float(self.end_x.text()), float(self.end_y.text())))
        #draw
        self.widget.canvas.ax.clear()
        self.widget.canvas.ax.grid(b=None, which='both', axis='both')
        obstacles =robot.getObstacles()
        for obs in obstacles:
            self.widget.canvas.ax.add_patch(obs.getDrawble("red"))
        self.widget.canvas.ax.plot([robot.getStartPoint().x], [robot.getStartPoint().y], 'ro', color = "blue"),
        self.widget.canvas.ax.annotate("start", xy=(robot.getStartPoint().x, robot.getStartPoint().y), xytext = (robot.getStartPoint().x, robot.getStartPoint().y + 0.2))
        self.widget.canvas.ax.plot([robot.getEndPoint().x], [robot.getEndPoint().y], 'ro', color = "blue")
        self.widget.canvas.ax.annotate("end", xy=(robot.getEndPoint().x, robot.getEndPoint().y), xytext = (robot.getEndPoint().x, robot.getEndPoint().y + 0.2))
        self.widget.canvas.ax.autoscale(enable=True, axis='both', tight=None)
        self.widget.canvas.ax.autoscale(enable=True, axis='both', tight=None)
        self.widget.canvas.draw()


    def reset_obstacle(self,robot):
        self.widget.canvas.ax.clear()
        self.widget.canvas.ax.grid(b=None, which='both', axis='both')
        obstacles = [Obstacle(MyPoint(random.randint(1, 20), random.randint(1, 10)), 0.5) for i in
                    range(obsNum)]
        robot.setObstacles(obstacles)
        for obs in obstacles:
            self.widget.canvas.ax.add_patch(obs.getDrawble("red"))
        self.widget.canvas.ax.autoscale(enable=True, axis='both', tight=None)
        self.widget.canvas.draw()
        print("show obs")


# Create GUI application

app = QtWidgets.QApplication(sys.argv)
form = Ui()
form.show()
app.exec_()






