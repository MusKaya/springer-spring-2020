## A python script and a shell wrapper to download the books made available by Springer during Spring 2020.

Note: It takes about 17GB of space (9GB for pdf files and 8GB for epub files) and may take a couple hours to download all files depending on your connection.


Via: https://group.springernature.com/gp/group/media/press-releases/freely-accessible-textbook-initiative-for-educators-and-students/17858180?utm_medium=social&utm_content=organic&utm_source=facebook&utm_campaign=SpringerNature_&sf232256230=1

### Usage

1) Clone or download & unzip the repository.
2) Open a terminal session and cd into the repository.

If you have downloaded it, probably:
```
cd $HOME/Downloads/springer-spring-2020-master
```
If you have cloned, you should know what to do.

3) Run the wrapper shell script:

To only get the pdf files:
```
bash catchem_all.sh
```

To get both pdf and epub files:
```
bash catchem_all.sh --type all
```

Just the epub files:
```
bash catchem_all.sh --type epub
```

4) Everything will be downloaded under the 'downloads' sub-directory.

If there are some files that couldn't be downloaded, then a couple excel
files will be created that list those files and related errors.

5) Thanks Springer!
