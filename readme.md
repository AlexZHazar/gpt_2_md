
# ChathGPT MHTML to Obsidian Markdown Converter

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

mapping is necessary to support md tags:

e.g. tag = "Apache/Pulsar" => HIERARCHICAL tag applied for original value "Pulsar"
e.g. tag = "ad-hoc"        => as is of                     original value "ad-hoc"
e.g. tag = "CI·CD"         => replace with SLASH for       original value "CI/CD"
e.g. tag = "Data_Vault"    => replace with SPACE for       original value "Data Vault"
other specific symbols are no allowed!

Case of the symbols is not important

Format of the list is important - leading tab is required for each line
