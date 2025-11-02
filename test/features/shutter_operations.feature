Feature: Shutter Operations
  As an observatory operator
  I want to open and close the dome shutter
  So that I can expose or protect the telescope and equipment

  Background:
    Given the dome controller is initialized
    And the dome is at home position
    And the shutter hardware is available

  Scenario: Open shutter from closed position
    Given the shutter is currently closed
    And the dome is at home position
    When I command the shutter to open
    Then the shutter should start opening
    And the shutter motor should run for the configured time
    And the shutter should reach the fully open position
    And the shutter status should show "open"

  Scenario: Close shutter from open position
    Given the shutter is currently open
    And the dome is at home position
    When I command the shutter to close
    Then the shutter should start closing
    And the shutter motor should run for the configured time
    And the shutter should reach the fully closed position
    And the shutter status should show "closed"

  Scenario: Attempt to operate shutter when dome not at home
    Given the dome is not at home position
    And the shutter is closed
    When I command the shutter to open
    Then the command should be rejected
    And an error should indicate dome must be at home
    And the shutter should remain in its current state

  Scenario: Shutter operation timeout
    Given the shutter is closed
    And the dome is at home position
    When I command the shutter to open
    And the operation exceeds the maximum time limit
    Then the shutter motor should be stopped
    And a timeout error should be reported
    And the shutter status should be marked as unknown

  Scenario: Emergency shutter stop
    Given the shutter is currently opening
    When I send an emergency stop command
    Then the shutter should stop immediately
    And the shutter motor should be powered off
    And the shutter position should be marked as intermediate

  Scenario: Shutter already in requested state
    Given the shutter is currently open
    When I command the shutter to open
    Then no motor movement should occur
    And a message should indicate shutter already open
    And the operation should complete successfully

  Scenario: Shutter limit switch failure
    Given the shutter limit switches are not functioning
    When I attempt to operate the shutter
    Then the operation should rely on timing only
    And the maximum time limit should be enforced
    And a warning should be logged about limit switch failure

  Scenario: Power failure during shutter operation
    Given the shutter is opening
    When power is lost to the shutter motor
    Then the shutter should stop in its current position
    And a power failure should be detected
    And the shutter status should be marked as unknown
    And manual recovery should be required
