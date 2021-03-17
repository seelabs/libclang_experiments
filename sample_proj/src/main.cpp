struct AStruct
{
    int i;
};

int
foo(bool b)
{
    if (b)
    {
        throw 0;
    }
    throw AStruct{0};
}

int
baz(bool b)
{
    foo(b);
}

int
bar(bool b)
{
    foo(b);
    bar(b);
    baz(b);
    throw 0;
    foo(b);
}

// int GLOBAL = [] { foo(true); };

int
main(int argc, char** argv)
{
    AStruct as{argc};
    try
    {
        try
        {
            foo(argc == 1);
        }
        catch (AStruct const&)
        {
            int decl_in_catch = 2;
            return decl_in_catch;
        }
        catch (int xxx)
        {
            // test rethrow
            throw;
        }
        catch (...)
        {
            return 1;
        }
    }
    catch (int y)
    {
        return 2;
    }
    foo(argc == 1);
    return 0;
}
