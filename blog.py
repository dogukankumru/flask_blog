from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps


#------------------------------------------------------------------------------------------------
#Kullanıcı girişinin yapılıp yapılmadığını kontrol eden decorator

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:                      #Eğer kullanıcı girişi yapılmışsa  bizim ilgili sayfayı açmamıza izin verilecek.
            return f(*args, **kwargs)
        
        else:
            flash("Bu sayfayı görüntülemek için lütfen giriş yapınız!","danger")         #Fakat kullanıcı girişi yapılmadan belirli bir sayfayı açmaya çalışıyosak
            return redirect(url_for("login"))                                            #ekranda bir hata mesajı gözükecek ve bizi giriş sayfasına yönlendirecek.
        
    return decorated_function

#-------------------------------------------------------------------------------------------------
#Makele formu olluşturmak için class oluşturuyoruz. 

class ArticleForm(Form):

    title = StringField("Makale Başlığı",validators=[validators.Length(min=3,max=100)])
    content= TextAreaField("Makale İçeriği")                                               #Makale içeriği uzun olacağı için TextAreaField ile oluşturduk.


#-------------------------------------------------------------------------------------------------
#Kullanıcı Kayıt formu için class oluşturuyoruz.

class RegisterForm(Form):
    name     = StringField("İsim ve Soyisim", validators=[validators.Length(min=4,max=35)])                                     #Kullanıcıdan isim-soyisim istedik ve bu bölüm 4 harften az - 35 harften fazla olamaz.
    username = StringField("Kullanıcı Adı", validators = [validators.Length(min=3,max=35)])
    email    = StringField("E-mail Adresiniz",validators=[validators.Email(message="Lütfen geçerli bir e-posta adresi giriniz.")])      #Kullanıcıdan e-mail adresi alıyor ve bu emailin geçerli olup olmadığını kontrol ediyor.

    password = PasswordField("Parola",validators=[validators.DataRequired(message="Lütfen parolayı giriniz."),
                                                  validators.EqualTo(fieldname="confirm",message="Parolanız uyuşmuyor.")])
    
    confirm  = PasswordField("Parolayı Doğrulayınız.")                                                                          #Parolayı aldık ve confirm password ile uyuşup uyuşmadığını kontrol ettik. Bununla beraber eğer parola alanı boş bırakılırsa bir hata mesajı verilecek.

#----------------------------------------------------------------------------------------------------

#Login formu için class oluşturuyoruz.

class LoginForm(Form):
    username = StringField("Kullanıcı Adı")
    password = PasswordField("Şifre")




#---------------------------------------------------------------------------------------

#Flaskı MySQL ile konfigüre etmiş olduk.

app = Flask(__name__)
app.secret_key = "dogukan-blog"

app.config["MYSQL_HOST"]="localhost"                #Kiralık sunucumuz olmadığı için yerel sunucuda oluşturuyoruz.
app.config["MYSQL_USER"]="root"                     #Sql sunucumuzun kullanıcı adı ve şifresini belirliyoruz.
app.config["MYSQL_PASSWORD"]=""
app.config["MYSQL_DB"]="dogukan_blog"
app.config["MYSQL_CURSORCLASS"]="DictCursor"

mysql = MySQL(app)

#---------------------------------------------------------------------------------------


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()
    sorgu = "SELECT * FROM articles"                        #Veritabanında makalaler tablosundaki bütün bilgileri alıyoruz ve bu veritabanında veri olup olmadığını kontrol ediyoruz.
    result = cursor.execute(sorgu)

    if result > 0:    #Eğer articles veritabanında makale varsa
        
        sozluk_makaleler = cursor.fetchall()   #Veritabanından gelen tüm makaleleri sozluk şeklinde geldiği için sozluk_makaleler'in içine koyduk.
        return render_template("articles.html",articles = sozluk_makaleler)
    
    else:
        return render_template("articles.html")   #Eğer veritabanında makale yoksa bize sadece makaleler sayfasını açacak işlem yapmadan.



@app.route("/article/<string:id>")
def article(id):                                            #Dinamik URL adresleri oluşturduk. Herbir makalemizi bu adreslere atayabiliriz böylece tekrar ve tekrar
                                                            #web-site oluşturmamıza gerek kalmadan otomatik oluşturulacak.
    cursor = mysql.connection.cursor()
    sorgu = "SELECT * FROM articles where id = %s"
    result = cursor.execute(sorgu,(id,))

    if result>0:   #Eğer belirtilen id numarasında bir makale varsa bizi /article/id sayfasının o id'deki makalesini gösterecek

        article = cursor.fetchone()  #Her id'de bir tane makale olabileceği için fetchall yerine fetchone kullanıldı.
        return render_template("article.html",article = article)
    
    else:  #Eğer belirtilen id numarası adına bir makale yoksa 
        return render_template("article.html")



@app.route("/register",methods = ["GET","POST"])                 #Get methodu: Belirtilen site ilk defa açıldığında karşımıza çıkacak olan sayfa
def register():                                                  #Post methodu ise aslında submit butonuna bastıktan sonra olacakları belirtiyor.

    form = RegisterForm(request.form)                            #Register sayfasında oluşturulan form doldurulduktan sonra ordan gelen bilgiler burdaki oluşturduğumuz classtaki bilgiler ile eşlececek.

    
    
    if request.method == "POST" and form.validate():
        
        isim = form.name.data
        kullanici_adi = form.username.data                             #Kayıt işlemi sırasında kullanıcının formdan doldurduğu bilgileri eğer bu bilgiler geçerliyse ve hata yoksa
        email = form.email.data                                        #kaydediyoruz.
        sifre = sha256_crypt.encrypt(form.password.data)
        
        
        cursor = mysql.connection.cursor()

       
        hesap_sorgulama = "SELECT * FROM users WHERE username = %s"
        result = cursor.execute(hesap_sorgulama,(kullanici_adi,))
        if result >0:                             
            flash("Bu kullanıcı adı kullanılmaktadır!","danger")                         #Aynı isimde kullanıcı adının bulunup bulunmadığını kontrol ediyoruz.
            return redirect(url_for("register"))                                         #Eğer aynı isimde kullanıcı adı kullanılmışsa hata verecek.
        
        else:
            mail_sorgulama = "SELECT * FROM users WHERE email = %s"                      #Aynı isimde e-mail adresinin bulunup bulunmadığını kontrol ediyoruz.
            sonuc = cursor.execute(mail_sorgulama,(email,))                              #Eğer aynı isimde e-mail kullanılmışsa hata verecek.
            if(sonuc>0):
                flash("Bu e-posta adresi kullanılmaktadır","danger")
                return redirect(url_for("register"))
            
            
            
            else:

                sorgu = "INSERT INTO users(name,email,username,password) VALUES(%s,%s,%s,%s)"         #Az önce kaydettiğimiz bilgileri sql veritabanına kaydettik.
                cursor.execute(sorgu,(isim,email,kullanici_adi,sifre))
                mysql.connection.commit()

                cursor.close()
                flash("Tebrikler! Başarıyla kayıt oldunuz...","success")      #Kayıt işlemi başarılı şeklinde flash mesajı yayınladık 
        
                return redirect(url_for("login"))                        #Redirect bizi istediğimiz bir url sayfasını açma imkanı sunuyor ve bunu url_for classıyla yapıyoruz ve anasayfaya dönmek istediğimizi belirtiyoruz butona tıkladıktan sonra. (index fonksiyonunu gerçekleştirmek istediğimizi belirttik)
    
    else:
        return render_template("register.html",form = form)      #Sayfa ilk defa açılıyor ise karşımıza register sayfası gelcek ve form karşımıza çıkacak.



@app.route("/login", methods = ["GET","POST"])
def login():

    giris_form = LoginForm(request.form)

    if request.method == "POST":
        
        username_entered = giris_form.username.data
        password_entered = giris_form.password.data
        
        cursor = mysql.connection.cursor()
        sorgu = "SELECT * FROM users WHERE username = %s"
        result = cursor.execute(sorgu,(username_entered,))

        if result > 0 :             #Eğer veritabanında kullanıcı adını bulabilmişse

            data = cursor.fetchone()    #Bulunan kullanıcı adına ait bilgileri "data" adında bir sözlüğe atıyoruz.
            real_password = data["password"]

            if sha256_crypt.verify(password_entered,real_password):  #Eğer veritabanında şifrelenmiş olan şifre ile giriş kısmında yazılan şifre aynı mı diye kontrol ediyor. Aynıysa TRUE döndürecek
                flash("Başarıyla Giriş Yaptınız.!","success")

                session["logged_in"] = True                         #Artık kullanıcı siteye giriş yaptığı için ona özel bir navigation bar gözükecek (Çıkış yap seçeneğinin bulunduğu ve diğer erişebileceği kullanıcıya özgü seçenekler)
                session["username"] = username_entered

                return redirect(url_for("index"))
            else:
                flash("Parolanızı Yanlış Girdiniz!","danger")        #Girilen parola ile veritabanındaki o kullanıcıya ait parola eşleşmezse hata mesajı çıkacak ve 
                return redirect(url_for("login"))                    #tekrardan login sayfasına geri dönecek.
         
        else:
            flash("Böyle bir kullanıcı bulunmamaktadır!","danger")  #Kullanıcının  girdiği kullanıcı adı veritabanında bulunmazsa hata mesajı çıkacak ve 
            return redirect(url_for("login"))                       #tekrardan login sayfasına geri dönecek.
    else:
        return render_template("login.html" , form = giris_form)    #Eğer GET emri ile websayfası ilk defa açıldıysa karşımıza form çıkacak.




@app.route("/logout")
def logout():
    session.clear()                                    #Kullanıcı Çıkış Yap seçeneğine tıklarsa, girmiş olduğu session temizlenecek ve anasayfaya yönlendirilecek.
    return redirect(url_for("index"))



@app.route("/dashboard")
@login_required                                  #Login_required decorator'ı ile bu sayfanın kullanıcı girişi yapılıp mı yapılmadan mı açılmaya çalışıldığını anlıyoruz.
def dashboard():
    
    cursor = mysql.connection.cursor()
    sorgu = "SELECT * FROM articles where author = %s"
    result = cursor.execute(sorgu,(session["username"],))         #Kontrol paneline bakan kullanıcının kendi adına makalesinin olup olmadığını kontrol ediyoruz.

    if result >0:       #Eğer kullanıcının makalesi varsa kullanıcının makaleleri kontrol panelinde gösterilecek.

        articles = cursor.fetchall()
        return render_template("dashboard.html", articles = articles)
    
    else:              #Eğer kullanıcının makalesi yoksa sadece sayfa açılacak
        return render_template("dashboard.html")



@app.route("/addarticle",methods=["GET","POST"])
def addarticle():                                                 #Kontrol panelinden makale ekle seçeneğine tıklandıktan eğer GET ile açıldıysa karşımıza form çıkacak
                                                                  
    makale_form = ArticleForm(request.form)
    
    if request.method == "POST" and makale_form.validate():

        makale_baslik = makale_form.title.data                   #Kullanıcının sitede girdiği makale başlığı ve makale içeriğini string değerlere atadık.
        makale_icerik = makale_form.content.data

        cursor = mysql.connection.cursor()
        sorgu = "INSERT INTO articles(title,author,content) VALUES(%s,%s,%s)"
        cursor.execute(sorgu,(makale_baslik,session["username"],makale_icerik))         #Veritabanımıza makale başlığını, makaleyi giren kullanıcı adını ve makale içeriğini giriyoruz.
        mysql.connection.commit()
        cursor.close()

        flash("Makale Başarıyla Eklendi!","success")
        return redirect(url_for("dashboard"))                                          #Makale başarıyla eklendikten sonra kullanıcıyı tekrardan kontrol paneline aktarıyoruz.

    
    else:            #Eğer siteyi ilk defa açıyorsak yani GET isteğiyle açmışsak

        return render_template("addarticle.html",form = makale_form)


@app.route("/delete/<string:id>")
@login_required                               #Makalemizi silebilmemiz için giriş yapmış olmamız gerekiyor.
def delete(id):
    
    cursor = mysql.connection.cursor()
    sorgu = "SELECT * FROM articles where author = %s and id = %s"       #Makaleyi silebilmemiz için aynı zamanda sadece kendi makalemizi silmemiz gerekiyor ve 
    result = cursor.execute(sorgu,(session["username"],id))              #silmek istediğimiz makalenin id'sinin varolması lazım.

    if result>0:

        sorgu2 = "DELETE FROM articles where id = %s"
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()                   #Silme işlemini gerçekleştiriyoruz ve tekrardan kontrol paneline dönüyor.
        return redirect(url_for("dashboard"))
    
    else:  #Eğer belirtilen makale kullanıcıya ait değilse veya o id numarasında makale yoksa
        flash("Böyle bir makale yok veya bu işleme yetkiniz bulunmamaktadır!","danger")
        return redirect(url_for("index"))


@app.route("/edit/<string:id>",methods = ["GET","POST"])
@login_required                                                                    #Makaleyi güncelleyebilmemiz için giriş yapmış olmamız gerekiyor.
def update(id):

    if request.method =="GET":  
                                                                                   #Eğer siteyi ilk defa açıyorsak bizim seçilen makale formunu otomatik olarak doldurup kullanıcıya göstermemiz gerekiyor.
        cursor = mysql.connection.cursor()                                         #ve kullanıcı hazır doldurulmuş olan makalesi üstünden değiştirmek istediği işlemleri yapabilir.
        sorgu = "SELECT * FROM articles where author = %s and id = %s"
        result = cursor.execute(sorgu,(session["username"],id)) 

        if result == 0:                                                            #Eğer güncellemek istediği makale kullanıcıya ait değilse veya belirtile id'de makale yoksa
            flash("Böyle bir makale yok veya bu makaleyi değiştirmeye yetkiniz yok!","danger")
            return redirect(url_for("index"))

        else:
            article = cursor.fetchone()
            form = ArticleForm()                          
            form.title.data = article["title"]                        #Güncellemek istediği formu oluşturuyoruz ve makalesini önüne sunuyoruz.
            form.content.data = article["content"]
            return render_template("update.html",form = form)

    else:   #Güncelle butonuna bastıktan sonra güncellenmiş olan makaleyi veritabanında da güncelliyoruz.

        form = ArticleForm(request.form)
        newTitle = form.title.data
        newContent = form.content.data

        cursor = mysql.connection.cursor()
        sorgu2 = "UPDATE articles SET title = %s, content = %s WHERE id = %s"

        cursor.execute(sorgu2,(newTitle,newContent,id))
        mysql.connection.commit()

        flash("Makale Başarıyla Güncellendi!","success")
        return redirect(url_for("dashboard"))  

@app.route("/search",methods =["GET","POST"])
def search():

    if request.method == "GET":   #Eğer kullanıcı /search adresine elle gitmeye çalışırsa (search kısmına bir şey yazmadan) otomatik olarak anasayfaya yönlendirilecek.
        return redirect(url_for("index"))

    else:
        kelime = request.form.get("keyword")   #search kısmına yazılan kelimeyi alacak
        cursor = mysql.connection.cursor()
        sorgu = "SELECT * FROM articles WHERE title LIKE '%" + kelime + "%'"   #sql like commandi ile aranan kelime makale başlığında geçiyor mu diye kontrol ediyoruz

        result = cursor.execute(sorgu)

        if result==0:  #Eğer yazılan kelime makale başlıklarıyla eşleşmediyse
            flash("Aranan kelimeye uygun makale bulunamadı","warning")
            return redirect(url_for("articles"))

        else:
            articles = cursor.fetchall()  #Aranan kelimeyle eşleşen tüm makaleleri articles'ın içine atıyoruz ve articles.html sayfasında gözükecek hepsi
            return render_template("articles.html",articles = articles)         
        

if __name__ =="__main__":
    app.run(debug=True)