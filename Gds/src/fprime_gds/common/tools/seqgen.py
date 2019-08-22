#!/usr/bin/env python
#===============================================================================
# NAME: tinyseqgen
#
# DESCRIPTION: A tiny sequence generator for F Prime. This sequence compiler takes a
# .seq file as input and produces a binary sequence file compatible with the
# F Prime sequence file loader and sequence file runner.
# AUTHOR: Kevin Dinkel
# EMAIL:  dinkel@jpl.nasa.gov
# DATE CREATED: December 15, 2015
#
# Copyright 2015, California Institute of Technology.
# ALL RIGHTS RESERVED. U.S. Government Sponsorship acknowledged.
#===============================================================================

import sys
import os
import copy
from optparse import OptionParser

from fprime.common.models.serialize.type_exceptions import *

__author__ = "Tim Canham"
__version__ = "1.0"
__email__ = "timothy.canham@jpl.nasa.gov"

# try:
from fprime_gds.common.models.common.command import Descriptor
from fprime_gds.common.models.common.command import Command
from fprime_gds.common.encoders.seq_writer import SeqBinaryWriter
from fprime_gds.common.loaders.cmd_xml_loader import CmdXmlLoader
from fprime_gds.common.data_types import exceptions as gseExceptions
from fprime_gds.common.parsers.seq_file_parser import SeqFileParser 

class SeqGenException(gseExceptions.GseControllerException):
    def __init__(self, val):
        super(SeqGenException,self).__init__(str(val))

# except:
#  __error("The Gse source code was not found in your $PYTHONPATH variable. Please set PYTHONPATH to something like: $BUILD_ROOT/Gse/src:$BUILD_ROOT/Gse/generated/$DEPLOYMENT_NAME")

def generateSequence(inputFile, outputFile, dictionary, timebase):
  '''
  Write a binary sequence file from a text sequence file
  @param inputFile: A text input sequence file name (usually a .seq extension)
  @param outputFile: An output binary sequence file name (usually a .bin extension)
  '''
  # Check the user environment:
  cmd_xml_dict = CmdXmlLoader()
  try:
    (cmd_id_dict, cmd_name_dict) = cmd_xml_dict.construct_dicts(dictionary)
  except gseExceptions.GseControllerUndefinedFileException:
    raise SeqGenException("Can't open file '" + dictionary + "'. ")

  # Parse the input file:
  command_list = []
  file_parser = SeqFileParser()
  for i, descriptor, seconds, useconds, mnemonic, args in file_parser.parse(inputFile):
    # Make sure that command is in the command dictionary:
    if mnemonic in cmd_name_dict:
      command_temp = copy.deepcopy(cmd_name_dict[mnemonic])
      # Set the command arguments:
      try:
        command_temp.setArgs(args)
      except ArgLengthMismatchException as e:
        raise SeqGenException("%d %s"%(i, "'" + mnemonic + "' argument length mismatch. " + e.getMsg()))
      except TypeException as e:
        raise SeqGenException("%d %s"%(i, "'" + mnemonic + "' argument type mismatch. " + e.getMsg()))
      # Set the command time and descriptor:
      command_temp.setDescriptor(descriptor)
      command_temp.setSeconds(seconds)
      command_temp.setUseconds(useconds)
      # Append this command to the command list:
      command_list.append(command_temp)
    else:
      raise SeqGenException("%d %s"%(i, "'" + mnemonic + "' does not match any command in the command dictionary."))
 
  # Write to the output file:
  writer = SeqBinaryWriter(timebase=timebase)
  if not outputFile:
    outputFile = os.path.splitext(inputFile)[0] + ".bin"
  try:
    writer.open(outputFile)
  except:
    raise SeqGenException("Encountered problem opening output file '" + outputFile + "'.")

  writer.write(command_list)
  writer.close()
  
  
help_text = "seqgen.py -d"

    
def main():
  '''
  The main program if run from the command line. Note that this file can also be used
  as a module by calling the generateSequence() function
  '''

  usage = "usage: %prog [options] input_file output_file"
  parser = OptionParser(usage=usage) 
  parser.add_option("-d", "--dictionary", dest="dictionary", action="store", type="string", \
                      help="Dictionary file name")
  parser.add_option("-t", "--timebase", dest="timebase", action="store", type="string", default = None, \
                      help="Set base path to generated command/telemetry definition files [default: any]")
  
  (opts, args) = parser.parse_args()
      
  if opts.timebase == None:
     timebase = 0xffff
  else:
     try:
        timebase = int(opts.timebase,0)
     except ValueError:
        print("Could not parse time base %s"%opts.timebase)
        return 1
     
  if (len(args) == 1 or len(args) == 2):
    inputfile = args[0]
    if len(args) == 1:
        outputfile = None
    try:
        generateSequence(inputfile,outputfile, opts.dictionary,timebase)
    except SeqGenException as e:
        print(e.getMsg())
        return 1
  else:
    parser.print_help()
    return 1
  return 0
  
  
if __name__ == "__main__":
  sys.exit(main())  