
<!DOCTYPE html>
<html lang="en-US">
  <head>
    <meta charset='utf-8'>
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="/assets/css/style.css?v=d13d26b6141eb1a3a0eb811a1e86befcd3a71c30">

<!-- Begin Jekyll SEO tag v2.5.0 -->
<title>Unpacking BattleEye - Article 1 | lolblat blog</title>
<meta name="generator" content="Jekyll v3.8.5" />
<meta property="og:title" content="Unpacking BattleEye - Article 1" />
<meta property="og:locale" content="en_US" />
<meta name="description" content="Research blog" />
<meta property="og:description" content="Research blog" />
<link rel="canonical" href="https://lolblat.github.io/articles/battle-eye-post-1.html" />
<meta property="og:url" content="https://lolblat.github.io/articles/battle-eye-post-1.html" />
<meta property="og:site_name" content="lolblat blog" />
<script type="application/ld+json">
{"@type":"WebPage","url":"https://lolblat.github.io/articles/battle-eye-post-1.html","headline":"Unpacking BattleEye - Article 1","description":"Research blog","@context":"http://schema.org"}</script>
<!-- End Jekyll SEO tag -->

  </head>

  <body>

    <header>
      <div class="container">
        <h1>lolblat blog</h1>
        <h2>Research blog</h2>

        <section id="downloads">
          
          <a href="https://github.com/lolblat/lolblat.github.io" class="btn btn-github"><span class="icon"></span>View on GitHub</a>
        </section>
      </div>
    </header>

    <div class="container">
      <section id="main_content">
        <h1 id="unpacking-battleeye---article-1">Unpacking BattleEye - Article 1</h1>

<h2 id="introduction">Introduction</h2>

<p>Hello everyone, this is the first article in a series of articles about unpacking and reversing BattleEye, the first few article will be about unpacking BattleEye application. This articles are work-in-progress articles.</p>

<p>Our target, the BattleEye application, is packed with VMProtect, we can figure it out after searching for past researches about BattleEye unpacking.</p>

<p>So what is VMProtect?, VMProtect is a commercial software that offers packing and protection for your application. VMProtect is a virtual machine packer, this is not like regular packers that compress the data of the application, and then decompress it in run time using the stub. The virtual machine packing is creating a virtual CPU with custom opcodes, and convert your application to be able to run on the created CPU. The VM based protection, is used to make the reverse engineering of the application extremely hard, because you need to find and reverse each opcode to know exactly what the application is doing.</p>

<h2 id="unpacking-the-protection">Unpacking the protection</h2>

<p>The packing is highly obfuscated, it has useless jumps and calls, it has lot of useless instruction that I needed to filter out.</p>

<p>After filtering out the useless instructions, we can create a quick summery about the VM itself, the VM is creating its own registers and its own stack, the stack is stored inside the EBP register, and the registers are stored inside the EDI register, the registers is an array on the original program stack (not on the VM stack), and the EDI register is the address of the array.</p>

<p>We have another 2 more important registers, we have the ESI register, that holds the VM instruction pointer, and we have the EBX register that holds the encryption key (we will take a look how it works and how it affect the program later).</p>

<p>We can split the VM operation to 3 steps: initialize the VM, getting and dispatching the command, and running the command.</p>

<p>Step 1: initialize the VM, in this step we are creating the stack of the VM, creating the registers array, storing the VM instruction pointer into the ESI register, and also creating the encryption key.</p>

<p>Step 2: where we are getting and dispatching the command, We are getting the opcode from the VM Instruction pointer, the opcode is the size of 1 byte, We are incrementing the VM Instruction pointer, after We have the opcode, We start to decode the opcode, We are XORing the opcode with the encryption key, and do some more mathematical operation on the opcode, then We are XORing the encryption key with the decoded opcode, We are getting the handler of the opcode from hander’s table, pushing the handler into the stack, and dispatching the opcode by returning into the handler.</p>

<p>Step 3: just running the command, and loop into the second step.</p>

<p>We are getting the command from the VM instruction pointer</p>

<p><img src="..\images\1569911824139.png" alt="first-image" /></p>

<p>We are getting the handler, and dispatching it.</p>

<p><img src="..\images\1569911974632.png" alt="second-image" /></p>

<h2 id="reverse-the-unpacking">Reverse the unpacking</h2>

<p>Now that we know how the VM is working, we can start to reverse engineering the opcodes and the application itself, I created an emulator to emulate the application, I passed over each opcode and reverse it.</p>

<p>The application loading <code class="highlighter-rouge">kernel32.dll</code>, and get the <code class="highlighter-rouge">VirtualProtect</code> function, afterwards changes the protection of the application segments, to be able to write to them, afterwards the application loading function, encrypt their loading address, and write it into the application. After all the loading, the application call <code class="highlighter-rouge">VirtualProtect</code> again on the application segments, and return their protection to their old ones.</p>

<p>The next step is that we return into unpacked code, the unpacked code is initializing global variables, the initializing code is using the loaded functions.</p>

<p>Most of the work in this part, was to reverse each opcode, and create the emulator.</p>

<h2 id="whats-next-and-used-tools">What’s next and used tools</h2>

<p>In light of this article representing the start of a series, you can expect more reversing and fun to come. I’ve came to the decision to create a debugger plugin for <code class="highlighter-rouge">x64dbg</code> to be able to debug the VM more easily, this plugin will be presented in the next article.</p>

<p>I will upload all my tools into my <a href="https://github.com/lolblat/Tools/tree/master/BattleEye">github</a></p>

<p>Thank you for reading :).</p>


      </section>
    </div>

    
      <script>
        (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
        (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
        m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
        })(window,document,'script','//www.google-analytics.com/analytics.js','ga');
        ga('create', 'UA-149123767-1', 'auto');
        ga('send', 'pageview');
      </script>
    
  </body>
</html>
