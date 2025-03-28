Imports System.IO
Imports Microsoft.Data.SqlClient

Module Program
    ' Your existing SQL Server connection
    Dim connectionString As String = "Server=sql-prod-targetlist-bge.database.windows.net;Database=targetlist-prod;User Id=BGE_DBWriter;Password=xxx;"

    Sub Main(args As String())
        Dim csvPath As String = "/home/deister/Dokumente/BIOSCAN/ARISE/targetlist.csv"

        Try
            Using connection As New SqlConnection(connectionString)
                connection.Open()

                Using reader As New StreamReader(csvPath)
                    Dim firstLine As Boolean = True

                    While Not reader.EndOfStream
                        Dim line As String = reader.ReadLine()

                        ' Skip the header line
                        If firstLine Then
                            firstLine = False
                            Continue While
                        End If

                        ' Split CSV values
                        Dim values As String() = line.Split(";"c)

                        If values.Length >= 13 Then
                            ' Prepare SQL command, but omit the ID column since it's automatically managed by the database
                            Dim query As String = "INSERT INTO TargetList (Kingdom, Phylum, Class, [Order], Family, Genus, Species, SpeciesTotal, AriseBarcodes, OtherBarcodes, SpeciesLocality, SpeciesOccurrenceStatus, DateCreated, DateModified) 
                                                  VALUES (@Kingdom, @Phylum, @Class, @Order, @Family, @Genus, @Species, @SpeciesTotal, @AriseBarcodes, @OtherBarcodes, @SpeciesLocality, @SpeciesOccurrenceStatus, @DateCreated, @DateModified)"

                            Using command As New SqlCommand(query, connection)
                                ' Add parameters
                                command.Parameters.AddWithValue("@Kingdom", values(1))
                                command.Parameters.AddWithValue("@Phylum", values(2))
                                command.Parameters.AddWithValue("@Class", values(3))
                                command.Parameters.AddWithValue("@Order", values(4))
                                command.Parameters.AddWithValue("@Family", values(5))
                                command.Parameters.AddWithValue("@Genus", values(6))
                                command.Parameters.AddWithValue("@Species", values(7))
                                command.Parameters.AddWithValue("@SpeciesTotal", Convert.ToInt32(values(8)))
                                command.Parameters.AddWithValue("@AriseBarcodes", Convert.ToInt32(values(9)))
                                command.Parameters.AddWithValue("@OtherBarcodes", Convert.ToInt32(values(10)))
                                command.Parameters.AddWithValue("@SpeciesLocality", values(11))
                                command.Parameters.AddWithValue("@SpeciesOccurrenceStatus", values(12))

                                command.Parameters.AddWithValue("@DateCreated", DateTime.Now)        
                                command.Parameters.AddWithValue("@DateModified", DateTime.Now)
                                ' Execute SQL command
                                command.ExecuteNonQuery()
                            End Using
                        End If
                    End While
                End Using

                Console.WriteLine("Data successfully imported into the database!")
            End Using

        Catch ex As Exception
            Console.WriteLine("Error: " & ex.Message)
        End Try
    End Sub
End Module
