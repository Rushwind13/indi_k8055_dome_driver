Feature: Dome Startup and Shutdown
  As an observatory operator
  I want to safely start up and shut down the dome system
  So that I can operate the observatory safely

  Background:
    Given the dome controller is available
    And the hardware is configured

  Scenario: Successful dome initialization
    When I initialize the dome controller
    Then the dome should be initialized successfully
    And the dome should not be at home position initially
    And the shutter should be in closed state initially
    And all hardware interfaces should be connected

  Scenario: Dome initialization with missing configuration
    Given the configuration file does not exist
    When I initialize the dome controller
    Then the dome should use default configuration
    And a warning should be displayed about missing configuration
    And the dome should still initialize successfully

  Scenario: Dome initialization in mock mode
    Given the dome is configured for mock mode
    When I initialize the dome controller
    Then the dome should initialize in mock mode
    And no actual hardware should be accessed
    And all operations should be simulated

  Scenario: Safe dome shutdown
    Given the dome is initialized and running
    When I shut down the dome controller
    Then the dome should move to home position
    And the shutter should be closed
    And all hardware interfaces should be disconnected
    And the dome should be in a safe state
