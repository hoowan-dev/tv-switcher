import tv_switcher


def test_main_runs(capsys):
    tv_switcher.main()
    assert capsys.readouterr().out
