import os
import scummbler_compiler

# Used to be in main, but put in a separate file so tests can use it.
def compile_script(infile, s_ver, outfilename):
    comp = scummbler_compiler.CompilerFactory(s_ver)
    
    print "Parsing \"" + infile + "\"..."
    results = comp.compileFile(infile)

    header = comp.generateHeader(len(results))
    
    if outfilename == None:
        outfilename = os.path.splitext(infile)[0] + "." + comp.getScriptType()
    try:
        print "Writing to " + outfilename
        outfile = file(outfilename, "wb")
        outfile.write(header + results)
        outfile.close()
    except Exception, e:
        print "Could not save to the file " + str(outfilename) + ", make sure the disk is not write-protected."
        raise e
