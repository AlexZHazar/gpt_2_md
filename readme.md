
# ChathGPT MHTML to Obsidian Markdown Converter


main.py:
1. save ChatGPT conversations as MHTML
2. convert MHTML to Markdown by this app

------

tag configuration in config.ini:

~~~
[Keywords]
words = 
	ad-hoc
	Ansible
    ...
~~~

mapping is necassary to support md tags:

e.g. tag = "Apache/Pulsar" => HIERARCHICAL tag applied for original value "Pulsar"
e.g. tag = "ad-hoc"        => as is of                     original value "ad-hoc"
e.g. tag = "CI·CD"         => replace with SLASH for       original value "CI/CD"
e.g. tag = "Data_Vault"    => replace with SPACE for       original value "Data Vault"
other specific symbols are no allowed!

Case of the symbols is not important

Format of the list is important - leading tab is required for each line

---------------------------------------------------------------------------

main_app2.py (obsolete): 
1. открываем нужную веб-страницу
2. в расширениях запускаем MarkDownload
3. долго ждём завершения
4. жмём "Download"
5. преобразуем этим приложением
6. перекидываем в нужную папку Obsidian