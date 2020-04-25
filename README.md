<h2><span style="color: #0000ff;"><em><strong>Unpacking BattleEye - Easy AntiCheat - Article 1</strong></em></span></h2>
<p><br /><span style="color: #ff9900;">Introduction</span></p>
<p>Hello everyone, this is the first article in a series of articles about unpacking and reversing BattleEye - Easy AntiCheat, the first few article will be about unpacking BattleEye - Easy AntiCheat application. This articles are work-in-progress articles.</p>
<p>Our target, the BattleEye - Easy AntiCheat application, is packed with VMProtect, we can figure it out after searching for past researches about BattleEye - Easy AntiCheat unpacking.</p>
<p>So what is VMProtect?, VMProtect is a commercial software that offers packing and protection for your application. VMProtect is a virtual machine packer, this is not like regular packers that compress the data of the application, and then decompress it in run time using the stub. The virtual machine packing is creating a virtual CPU with custom opcodes, and convert your application to be able to run on the created CPU. The VM based protection, is used to make the reverse engineering of the application extremely hard, because you need to find and reverse each opcode to know exactly what the application is doing.</p>
<p><strong><span style="color: #ff9900;">Unpacking the protection</span></strong><br />The packing is highly obfuscated, it has useless jumps and calls, it has lot of useless instruction that I needed to filter out.</p>
<p>After filtering out the useless instructions, we can create a quick summery about the VM itself, the VM is creating its own registers and its own stack, the stack is stored inside the EBP register, and the registers are stored inside the EDI register, the registers is an array on the original program stack (not on the VM stack), and the EDI register is the address of the array.</p>
<p>We have another 2 more important registers, we have the ESI register, that holds the VM instruction pointer, and we have the EBX register that holds the encryption key (we will take a look how it works and how it affect the program later).</p>
<p>We can split the VM operation to 3 steps: initialize the VM, getting and dispatching the command, and running the command.</p>
<p>Step 1: initialize the VM, in this step we are creating the stack of the VM, creating the registers array, storing the VM instruction pointer into the ESI register, and also creating the encryption key.</p>
<p>Step 2: where we are getting and dispatching the command, We are getting the opcode from the VM Instruction pointer, the opcode is the size of 1 byte, We are incrementing the VM Instruction pointer, after We have the opcode, We start to decode the opcode, We are XORing the opcode with the encryption key, and do some more mathematical operation on the opcode, then We are XORing the encryption key with the decoded opcode, We are getting the handler of the opcode from hander&rsquo;s table, pushing the handler into the stack, and dispatching the opcode by returning into the handler.</p>
<p>Step 3: just running the command, and loop into the second step.</p>
<p>We are getting the command from the VM instruction pointer</p>
<p><img src="https://lolblat.github.io/images/1569911824139.png" alt="first-image" /></p>
<p>We are getting the handler, and dispatching it.</p>
<p><img src="https://lolblat.github.io/images/1569911974632.png" alt="second-image" /></p>
<p><strong><span style="color: #ff9900;">Reverse the unpacking</span></strong><br />Now that we know how the VM is working, we can start to reverse engineering the opcodes and the application itself, I created an emulator to emulate the application, I passed over each opcode and reverse it.</p>
<p>The application loading kernel32.dll, and get the VirtualProtect function, afterwards changes the protection of the application segments, to be able to write to them, afterwards the application loading function, encrypt their loading address, and write it into the application. After all the loading, the application call VirtualProtect again on the application segments, and return their protection to their old ones.</p>
<p>The next step is that we return into unpacked code, the unpacked code is initializing global variables, the initializing code is using the loaded functions.</p>
<p>Most of the work in this part, was to reverse each opcode, and create the emulator.</p>
<p>What&rsquo;s next and used tools<br />In light of this article representing the start of a series, you can expect more reversing and fun to come. I&rsquo;ve came to the decision to create a debugger plugin for x64dbg to be able to debug the VM more easily, this plugin will be presented in the next article.</p>
<p>I will upload all my tools into my Github : https://github.com/zodiacddos/BattleEye - Easy AntiCheat-EasyAntiCheat-Bypasses/</p>
<p>Thank you for reading :).</p>
<p>Cc: lolbat</p>
<!-- #######  YAY, I AM THE SOURCE EDITOR! #########-->
<h1 style="color: #5e9ca0;">You can edit <span style="color: #2b2301;">this demo</span> text!</h1>
<h2 style="color: #2e6c80;">How to use the editor:</h2>
<p>Paste your documents in the visual editor on the left or your HTML code in the source editor in the right. <br />Edit any of the two areas and see the other changing in real time.&nbsp;</p>
<p>Click the <span style="background-color: #2b2301; color: #fff; display: inline-block; padding: 3px 10px; font-weight: bold; border-radius: 5px;">Clean</span> button to clean your source code.</p>
<h2 style="color: #2e6c80;">Some useful features:</h2>
<ol style="list-style: none; font-size: 14px; line-height: 32px; font-weight: bold;">
<li style="clear: both;"><img style="float: left;" src="https://html-online.com/img/01-interactive-connection.png" alt="interactive connection" width="45" /> Interactive source editor</li>
<li style="clear: both;"><img style="float: left;" src="https://html-online.com/img/02-html-clean.png" alt="html cleaner" width="45" /> HTML Cleaning</li>
<li style="clear: both;"><img style="float: left;" src="https://html-online.com/img/03-docs-to-html.png" alt="Word to html" width="45" /> Word to HTML conversion</li>
<li style="clear: both;"><img style="float: left;" src="https://html-online.com/img/04-replace.png" alt="replace text" width="45" /> Find and Replace</li>
<li style="clear: both;"><img style="float: left;" src="https://html-online.com/img/05-gibberish.png" alt="gibberish" width="45" /> Lorem-Ipsum generator</li>
<li style="clear: both;"><img style="float: left;" src="https://html-online.com/img/6-table-div-html.png" alt="html table div" width="45" /> Table to DIV conversion</li>
</ol>
<p>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p>
<h2 style="color: #2e6c80;">Cleaning options:</h2>
<table class="editorDemoTable">
<thead>
<tr>
<td>Name of the feature</td>
<td>Example</td>
<td>Default</td>
</tr>
</thead>
<tbody>
<tr>
<td>Remove tag attributes</td>
<td><img style="margin: 1px 15px;" src="images/smiley.png" alt="laughing" width="40" height="16" /> (except <strong>img</strong>-<em>src</em> and <strong>a</strong>-<em>href</em>)</td>
<td>&nbsp;</td>
</tr>
<tr>
<td>Remove inline styles</td>
<td><span style="color: green; font-size: 13px;">You <strong style="color: blue; text-decoration: underline;">should never</strong>&nbsp;use inline styles!</span></td>
<td><strong style="font-size: 17px; color: #2b2301;">x</strong></td>
</tr>
<tr>
<td>Remove classes and IDs</td>
<td><span id="demoId">Use classes to <strong class="demoClass">style everything</strong>.</span></td>
<td><strong style="font-size: 17px; color: #2b2301;">x</strong></td>
</tr>
<tr>
<td>Remove all tags</td>
<td>This leaves <strong style="color: blue;">only the plain</strong> <em>text</em>. <img style="margin: 1px;" src="images/smiley.png" alt="laughing" width="16" height="16" /></td>
<td>&nbsp;</td>
</tr>
<tr>
<td>Remove successive &amp;nbsp;s</td>
<td>Never use non-breaking spaces&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;to set margins.</td>
<td><strong style="font-size: 17px; color: #2b2301;">x</strong></td>
</tr>
<tr>
<td>Remove empty tags</td>
<td>Empty tags should go!</td>
<td>&nbsp;</td>
</tr>
<tr>
<td>Remove tags with one &amp;nbsp;</td>
<td>This makes&nbsp;no sense!</td>
<td><strong style="font-size: 17px; color: #2b2301;">x</strong></td>
</tr>
<tr>
<td>Remove span tags</td>
<td>Span tags with <span style="color: green; font-size: 13px;">all styles</span></td>
<td><strong style="font-size: 17px; color: #2b2301;">x</strong></td>
</tr>
<tr>
<td>Remove images</td>
<td>I am an image: <img src="images/smiley.png" alt="laughing" /></td>
<td>&nbsp;</td>
</tr>
<tr>
<td>Remove links</td>
<td><a href="https://html-online.com">This is</a> a link.</td>
<td>&nbsp;</td>
</tr>
<tr>
<td>Remove tables</td>
<td>Takes everything out of the table.</td>
<td>&nbsp;</td>
</tr>
<tr>
<td>Replace table tags with structured divs</td>
<td>This text is inside a table.</td>
<td>&nbsp;</td>
</tr>
<tr>
<td>Remove comments</td>
<td>This is only visible in the source editor <!-- HELLO! --></td>
<td><strong style="font-size: 17px; color: #2b2301;">x</strong></td>
</tr>
<tr>
<td>Encode special characters</td>
<td><span style="color: red; font-size: 17px;">&hearts;</span> <strong style="font-size: 20px;">☺ ★</strong> &gt;&lt;</td>
<td><strong style="font-size: 17px; color: #2b2301;">x</strong></td>
</tr>
<tr>
<td>Set new lines and text indents</td>
<td>Organize the tags in a nice tree view.</td>
<td>&nbsp;</td>
</tr>
</tbody>
</table>
<p><strong>&nbsp;</strong></p>
<p><strong>Save this link into your bookmarks and share it with your friends. It is all FREE! </strong><br /><strong>Enjoy!</strong></p>
<p><strong>&nbsp;</strong></p>
