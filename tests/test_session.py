# ATtila
# Developed by Christian Visintin
# 
# MIT License
# Copyright (c) 2019 Christian Visintin
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import unittest

from attila.atsession import ATSession
from attila.atcommand import ATCommand

class TestSession(unittest.TestCase):

  def __init__(self, methodName):
    super().__init__(methodName)
    self.__test_collectables()
    self.__test_commands_operations()
    self.__test_doppelganger()
    self.__test_exec_and_validate()
    self.__test_session_values()

  def __test_session_values(self):
    """
    Test set/get session values
    """
    session = ATSession()
    #Try with not existing key
    with self.assertRaises(KeyError):
      session.get_session_value("foobar")
    session.set_session_value("foo", "bar")
    self.assertEqual(session.get_session_value("foo"), "bar", "get_session_value failed; expected 'bar' got %s" % session.get_session_value("foo"))

  def __test_exec_and_validate(self):
    """
    Test ATSession just adding a command and evaluating its response
    """
    session = ATSession()
    simple_command = ATCommand("AT", "OK")
    session.add_command(simple_command)
    next_command = session.get_next_command()
    #Prepare a response for it; in this case we'll simulate a successful response
    serial_response = ["OK"]
    response = session.validate_response(serial_response, 100)
    print("%s (expected %s) has response: %s" % (next_command.command, next_command.expected_response, response.full_response))
    self.assertFalse(session.last_command_failed)
    self.assertEqual(response.response, "OK", "Command should have OK as response but has %s" % response.response)
    #Let's simulate a command that will fail
    simple_command2 = ATCommand("AT+CGDCONT=1, \"IP\", \"internet.foo.bar\"", "OK")
    session.add_command(simple_command2)
    next_command = session.get_next_command()
    #Prepare a response for it; in this case we'll simulate a bad response
    serial_response = ["ERROR"]
    response = session.validate_response(serial_response, 100)
    print("%s (expected %s) has response: %s" % (next_command.command, next_command.expected_response, response.full_response))
    self.assertTrue(session.last_command_failed)
    #Regex in response
    #Let's get the device serial, imagine that all the device has a serial number of 16 hex digits
    gsn_command = ATCommand("AT+GSN", "^[0-9,A-F]{16}$")
    session.add_command(gsn_command)
    next_command = session.get_next_command()
    #Prepare a response for it; in this case we'll simulate a successful response
    serial_response = ["AC03C7F3D2EB7832", "OK"]
    response = session.validate_response(serial_response, 100)
    print("%s (expected %s) has response: %s" % (next_command.command, next_command.expected_response, response.full_response))
    self.assertFalse(session.last_command_failed)
    self.assertEqual(response.response, "AC03C7F3D2EB7832", "Command should have AC03C7F3D2EB7832 as response but has %s" % response.response)
    #Bad cases
    #Not existing session key
    command_not_replaceable = ATCommand("AT+CGDATA=${CONTEXT}", "OK")
    session.add_command(command_not_replaceable)
    self.assertIsNotNone(session.get_next_command())
    serial_response = ["+CME: ERRROR"]
    response = session.validate_response(serial_response, 100)
    print("%s (expected %s) has response: %s" % (next_command.command, next_command.expected_response, response.full_response))
    self.assertTrue(session.last_command_failed)

  def __test_commands_operations(self):
    session = ATSession([])
    #Add commands
    self.assertTrue(session.add_new_command("AT", "OK"), "add_new_command failed")
    #Bad case
    self.assertFalse(session.add_new_command(None, None), "add_new_command failed")
    #Rem commands
    self.assertTrue(session.rem_command(0), "Could not remove command 0")
    self.assertFalse(session.rem_command(500), "Should have failed, but didn't in trying to remove command 500")
    #Get next command
    self.assertTrue(session.add_new_command("AT", "OK"), "add_new_command failed")
    self.assertIsNotNone(session.get_next_command(), "Command shouldn't be None")
    self.assertTrue(session.rem_command(0), "Could not remove command 0")
    #Bad case next command
    self.assertIsNone(session.get_next_command(), "Get next command should be None")
    #Get command
    self.assertTrue(session.add_new_command("AT", "OK"), "add_new_command failed")
    self.assertIsNotNone(session.get_command(0), "Command at 0 shouldn't be None")
    self.assertIsNone(session.get_command(5), "Command at 5 should be None")

  def __test_collectables(self):
    """
    Test collectables feature in ATSession using AT+CSQ
    """
    session = ATSession()
    csq_command = ATCommand("AT+CSQ", "OK", 10, 0, ["AT+CSQ=?{rssi},"])
    session.add_command(csq_command)
    #Let's get command
    next_command = session.get_next_command()
    #Invent a response for it
    serial_response = ["AT+CSQ=31,1", "OK"]
    response = session.validate_response(serial_response, 50)
    print("%s (expected %s) has response: %s" % (next_command.command, next_command.expected_response, response.full_response))
    #Last command should have succeded
    self.assertFalse(session.last_command_failed)
    #Verify if collectable has actually been collected
    try:
      rssi = session.get_session_value("rssi")
      self.assertEqual(rssi, 31, "rssi should be 31, but is %s" % rssi)
    except KeyError as err:
      raise err
    print("RSSI from AT+CSQ: %d" % rssi)
    #Let's try a collectable which searches for 15 digits (for getting the IMEI for example) => ^[0-9]{15}$
    imei_command = ATCommand("AT+CGSN", "OK", 10, 0, ["?{IMEI::^[0-9]{15}$}"])
    session.add_command(imei_command)
    #Let's get command
    next_command = session.get_next_command()
    #Invent a response for it
    serial_response = ["AT+CGSN", "123456789012345", "OK"]
    response = session.validate_response(serial_response, 50)
    print("%s (expected %s) has response: %s" % (next_command.command, next_command.expected_response, response.full_response))
    #Last command should have succeded
    self.assertFalse(session.last_command_failed)
    #Verify if collectable has actually been collected
    try:
      imei = session.get_session_value("IMEI")
      self.assertEqual(imei, 123456789012345, "rssi should be '123456789012345', but is %s" % imei)
    except KeyError as err:
      raise err
    print("IMEI from AT+CGSN: %d" % imei)
    #Combining line content with key regex and session keys
    #Look for both rssi and ber, but use key regex and session values
    csq_command = ATCommand("AT+CSQ", "OK", 10, 0, ["AT+CSQ=?{rssi::[0-9]{1,2}},","AT+CSQ=${rssi},?{ber::[0-9]{1,2}}"])
    session.add_command(csq_command)
    #Let's get command
    next_command = session.get_next_command()
    #Invent a response for it
    serial_response = ["AT+CSQ=31,2", "OK"]
    response = session.validate_response(serial_response, 50)
    print("%s (expected %s) has response: %s" % (next_command.command, next_command.expected_response, response.full_response))
    #Last command should have succeded
    self.assertFalse(session.last_command_failed)
    #Verify if collectable has actually been collected
    try:
      rssi = session.get_session_value("rssi")
      self.assertEqual(rssi, 31, "rssi should be 31, but is %s" % rssi)
      ber = session.get_session_value("ber")
      self.assertEqual(ber, 2, "ber should be 2, but is %s" % ber)
    except KeyError as err:
      raise err
    print("RSSI from AT+CSQ: %d; ber from AT+CSQ: %d" % (rssi, ber))
    #Not existing collectable in response
    csq_command = ATCommand("AT+CSQ", "OK", 10, 0, ["AT+CSQ=?{RSSI::[0-9]{1,2}},","AT+CSQ=${RSSI},?{ber::[0-9]{1,2}}"])
    session.add_command(csq_command)
    #Let's get command
    next_command = session.get_next_command()
    #Invent a response for it
    serial_response = ["AT+CSQDAFAQ", "OK"]
    response = session.validate_response(serial_response, 50)
    print("%s (expected %s) has response: %s" % (next_command.command, next_command.expected_response, response.full_response))
    #Last command should have succeded
    self.assertFalse(session.last_command_failed)
    #Verify if collectable has actually been collected
    with self.assertRaises(KeyError):
      session.get_session_value("RSSI")
    #Collectable test OK

  def __test_doppelganger(self):
    """
    Test doppelganger feature in ATSession using AT+CPIN
    """
    session = ATSession()
    #First prepare its doppelganger
    cpin_enter_pin = ATCommand("AT+CPIN=${SIM_PIN}", "OK")
    #Let's define an AT Command (AT+CPIN?)
    cpin_command = ATCommand("AT+CPIN?", "READY", 10, 0, None, cpin_enter_pin)
    #Add command to session
    session.add_command(cpin_command)
    #Add SIM PIN to session storage
    sim_pin = 7782
    session.set_session_value("SIM_PIN", 7782)
    #Verify session storage
    read_pin = session.get_session_value("SIM_PIN")
    self.assertEqual(sim_pin, read_pin, "SIM PIN should be %d, but is %d" % (sim_pin, read_pin))
    #Get command
    next_command = session.get_next_command()
    #Verify command
    self.assertEqual(next_command.command, "AT+CPIN?", "Next command should be AT+CPIN?, but is %s" % next_command.command)
    #Let's create a fake response
    serial_response = ["CPIN:SIM PIN", "OK"]
    response = session.validate_response(serial_response, 100)
    #Last command should have failed (we expected READY)
    self.assertTrue(session.last_command_failed)
    self.assertEqual(response.full_response, serial_response, "Response associated to command is different from the response got from serial device")
    print("%s (expected %s) has response: %s" % (next_command.command, next_command.expected_response, response.full_response))
    #Let's get the next command, that should be the doppelganger
    next_command = session.get_next_command()
    self.assertEqual(next_command.command, "AT+CPIN=%d" % sim_pin, "The next command should be the doppelganger, but is %s" % next_command.command)
    print("Next command is doppelganger with replaced session value: %s" % next_command.command)
    #Let's invent a response for it, let's say it's OK
    serial_response = ["OK"]
    response = session.validate_response(serial_response, 100)
    #Last command should have succeded
    self.assertFalse(session.last_command_failed)
    print("%s (expected %s) has response: %s" % (next_command.command, next_command.expected_response, response.response))
    self.assertEqual(response.response, next_command.expected_response, "The response should be OK, but is %s" % response.response)

if __name__ == "__main__":
  unittest.main()
