# ReadMe Liquid

Microsoft Liquid uses F# and seems best used with Visual Studio. I therefore installed it on Windows (10) by git cloning their [repository](https://github.com/StationQ/Liquid) and following the instructions in [GettingStarted.md](https://github.com/StationQ/Liquid/blob/master/GettingStarted.md).

There is a template in the source directory, Liquid.snl, which I opened in Visual Studio and adapted to implement the Shor code. Under Project -> Liquid Properties..., in the Debug section the command line argument __ShorCode() should be supplied to correctly call our code.

The program can be tested with Ctrl-F5, this keeps the output window open after execution so the user can check for errors.