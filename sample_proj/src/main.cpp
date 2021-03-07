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

int
main(int argc, char** argv)
{
    AStruct as{argc};
    try
    {
        foo(argc == 1);
    }
    catch (...)
    {
        return 1;
    }
    foo(argc == 1);
    return 0;
}
