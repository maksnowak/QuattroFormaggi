def run():
    import asyncio
    from dotenv import load_dotenv
    from quattroformaggi.QueryInterpreter import interpret_query

    load_dotenv()

    result = asyncio.run(interpret_query("show underfunded food crises in the Sahel since 2022"))
    print(result)
