#!/usr/bin/env python3

"""
Implementation of a simple client that is able to accomplish the following:

- Retrieve a GamePrx from a configuration file and connect to it
- Serve a Player servant
- Receive the invocations to create robot controllers
- Receive the win, lose or gameAbort invocation at the end of a match
- The 4 robot controllers behave in the same way

This implementation lacks:

- The RobotController servants are in the same process as the Player, so
  it breaks a practice requisite
- No detector controllers are created
- No mine positions are returned to the game
- There is no communication between the robot controllers
"""

import sys

import Ice



Ice.loadSlice('robots.ice --all -I .')
import robots
import drobots
#from detectorcontroller import *
from robotcontroller import *

class GameApp(Ice.Application):
    """
    Ice.Application specialization
    """

    def run(self, argv):
        """
        Entry-point method for every Ice.Application object.
        """

        broker = self.communicator()

        # Using PlayerAdapter object adapter forces to define a config file
        # where, at least, the property "PlayerAdapter.Endpoints" is defined
        adapter = broker.createObjectAdapter("PlayerAdapter")

        # Using "propertyToProxy" forces to define the property "GameProxy"
        game_prx = broker.propertyToProxy("GameProxy")
        game_prx = drobots.GamePrx.checkedCast(game_prx)

        # Using "getProperty" forces to define the property "PlayerName"
        name = broker.getProperties().getProperty("PlayerName")



        servant = PlayerI(broker,adapter)	
        player_prx = adapter.addWithUUID(servant)
        player_prx = drobots.PlayerPrx.uncheckedCast(player_prx)
        adapter.activate()

        #proxy_game = broker.propertyToProxy('Player') 
        ##game = drobots.GamePrx.checkedCast(proxy_game)
        #gameFact = drobots.GameFactoryPrx.checkedCast(proxy_game)
        #game = gameFact.makeGame("GameRobots", 2)

        try:
            print("Connecting to game {} with nickname {}".format(game_prx, name))
            game_prx.login(player_prx, name)

            self.shutdownOnInterrupt()
            self.communicator().waitForShutdown()

        except drobots.GameInProgress:
            print("\nGame already in progress in this room. Please try another room.")
            return 1
        except drobots.InvalidName:
            print("\nThis player name is already taken or invalid. Please change it.")
            return 2
        except drobots.InvalidProxy:
            print("\nInvalid proxy. Please try again.")
            return 3
        except drobots.BadNumberOfPlayers:
            print("\nIncorrect number of players for a game. Please try another room.")
            return 4

        self.shutdownOnInterrupt()
        broker.waitForShutdown()
        return 0

class PlayerI(drobots.Player):
    """
    Player interface implementation.

    It responds correctly to makeController, win, lose or gameAbort.
    """
    def __init__(self,broker, adapter):
        self.adapter = adapter
        self.broker = broker
        self.factory = self.createContainerFactories()
        self.container = self.createContainerControllers()
        self.dcontroller = None#self.createDetectorController()
        #self.detector_controller = None
        self.counter = 0
        self.mine_index = 0
        self.mines = [
            drobots.Point(x=100, y=100),
            drobots.Point(x=100, y=300),
            drobots.Point(x=300, y=100),
            drobots.Point(x=300, y=300),
        ]

    def createContainerFactories(self):
        string_prx = 'container -t -e 1.1:tcp -h localhost -p 9190 -t 60000'
        container_proxy = self.broker.stringToProxy(string_prx)
        factories_container = robots.ContainerPrx.checkedCast(container_proxy)
        factories_container.setType("ContainerFactories")
        print( "Creating factories....")
        for i in range(0,):
            string_prx = 'Factory -t -e 1.1:tcp -h localhost -p 909'+str(i)+' -t 60000'
            factory_proxy = self.broker.stringToProxy(string_prx)
            print (factory_proxy)
            factory = drobots.FactoryPrx.checkedCast(factory_proxy)
            
            if not factory:
                raise RuntimeError('Invalid factory '+str(i)+' proxy')
        
            factories_container.link(i, factory_proxy)
        
        return factories_container

    def createContainerControllers(self):
        container_proxy = self.broker.stringToProxy('container -t -e 1.1:tcp -h localhost -p 9190 -t 60000')
        controller_container = robots.ContainerPrx.checkedCast(container_proxy)
        controller_container.setType("ContainerController")

        if not controller_container:
            raise RuntimeError('Invalid factory proxy')
        
        return controller_container
    def createDetectorController(self):
        detector_proxy = self.broker.stringToProxy('Detector -t -e 1.1:tcp -h localhost -p 9093 -t 60000')
        detector_factory = robots.ContainerPrx.uncheckedCast(detector_proxy)
        detector_factory.setType("Detector")

        if not controller_container:
            raise RuntimeError('Invalid factory proxy')
        
        return detector_factory

    def makeController(self, bot, current):

        i=self.counter%3
	    print("robot en {}".format(str(i)))
        fact_prox=self.factory.getElementAt(i)
	    print (fact_prox)
	    factory=robots.ControllerFactoryPrx.checkedCast(fact_prox)
	    rc=factory.make(robot,self.container_robots,self.counter)
	    self.counter += 1
	    return rc

        
    def makeDetectorController(self, current):
        """
        Pending implementation:
        DetectorController* makeDetectorController();
        """
        print("Make detector controller.")

        if self.detector_controller is not None:
            return self.detector_controller

        controller = makeController(container)
        object_prx = current.adapter.addWithUUID(controller)
        self.detector_controller = \
            drobots.DetectorControllerPrx.checkedCast(object_prx)
        return self.detector_controller

    def getMinePosition(self, current):

        pos = self.mines[self.mine_index]
        self.mine_index += 1
        return pos

    def win(self, current):

        print("You win")
        current.adapter.getCommunicator().shutdown()

    def lose(self, current):

        print("You lose :-(")
        current.adapter.getCommunicator().shutdown()

    def gameAbort(self, current):

        print("The game was aborted")
        current.adapter.getCommunicator().shutdown()

    def remove_robots(self):
        container = self.robot_container.list()
        for robot_id in container:
            self.robot_container.unlink(robot_id)


if __name__ == '__main__':
    client = GameApp()
    retval = client.main(sys.argv)
    sys.exit(retval)
